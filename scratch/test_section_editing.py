import unittest
import json
import os
import sys
import io

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app
from database import get_db, init_db, q, execute

class TestSectionEditingAndPdf(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_client_company_locking_and_section_editing(self):
        camoor_user = q("SELECT id, company_id FROM users WHERE role = 'client' AND email = 'safety@camoorblinds.com'", one=True)
        if not camoor_user:
            camoor_co = q("SELECT id FROM companies WHERE name LIKE '%Camoor%'", one=True)
            camoor_uid = execute(
                "INSERT INTO users (name, email, password_hash, role, company_id, created_at) VALUES (?,?,?,?,?,?)",
                ("Camoor Client", "safety@camoorblinds.com", "dummy", "client", camoor_co['id'], "2026-08-18T12:00:00")
            )
            camoor_cid = camoor_co['id']
        else:
            camoor_uid = camoor_user['id']
            camoor_cid = camoor_user['company_id']

        with self.client.session_transaction() as sess:
            sess['user_id'] = camoor_uid

        # 1. Fetch osh_new page - verify only Camoor company is available
        res = self.client.get('/portal/oshwa/new')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Camoor Blinds Sdn. Bhd.', res.data)
        # Shouldn't show other company dropdown options to client
        self.assertIn(b'type="hidden" name="company_id"', res.data)

        # 2. Create new report as client with custom section content
        toc_with_custom_content = [
            {
                "id": "sec_01",
                "title": "ABREVIATION / SINGKATAN",
                "page": 1,
                "icon": "🔤",
                "is_header": True,
                "content": "Custom test abbreviation content written by client before saving."
            },
            {
                "id": "sec_02",
                "title": "1.0 BACKGROUND",
                "page": 2,
                "icon": "🏢",
                "is_header": True,
                "content": "Audit observations on premise background: Located in Valdor Industrial area."
            }
        ]

        post_res = self.client.post('/portal/oshwa/new', data={
            'title': 'Test Client Editable OSHWA Dossier',
            'company_id': camoor_cid,
            'category': 'Full Safety Manual',
            'ref_no': 'TM/TEST/2026/01',
            'revision': 'Rev 1.0',
            'status': 'Draft',
            'sections_json': json.dumps(toc_with_custom_content)
        }, follow_redirects=False)

        self.assertEqual(post_res.status_code, 302)
        new_url = post_res.headers['Location']
        # Extract report oid
        oid = int(new_url.split('/portal/oshwa/')[1].split('/view')[0])

        # 3. Test saving single section via AJAX
        save_single_res = self.client.post(f'/portal/oshwa/{oid}/save-section', json={
            'id': 'sec_01',
            'content': 'UPDATED client text for abbreviation section after live edit!'
        })
        self.assertEqual(save_single_res.status_code, 200)
        data = save_single_res.get_json()
        self.assertTrue(data.get('ok'))

        # 4. Test re-compiling PDF
        compile_res = self.client.get(f'/portal/oshwa/{oid}/compile-pdf', follow_redirects=False)
        self.assertEqual(compile_res.status_code, 302)

        # 5. Test downloading dynamic PDF
        download_res = self.client.get(f'/portal/oshwa/{oid}/download')
        self.assertEqual(download_res.status_code, 200)
        self.assertEqual(download_res.mimetype, 'application/pdf')
        self.assertTrue(len(download_res.data) > 1000)

        # 6. Verify isolation: Top Glove / Top Chemical client cannot edit or view this report
        tg_user = q("SELECT id FROM users WHERE email = 'client@topglove.com'", one=True)
        with self.client.session_transaction() as sess:
            sess['user_id'] = tg_user['id']

        unauth_view = self.client.get(f'/portal/oshwa/{oid}/view')
        self.assertEqual(unauth_view.status_code, 403)

        unauth_save = self.client.post(f'/portal/oshwa/{oid}/save-section', json={
            'id': 'sec_01',
            'content': 'Hacked content'
        })
        self.assertEqual(unauth_save.status_code, 403)

        print("=== ALL SECTION EDITING & PDF COMPILATION TESTS PASSED ===")

if __name__ == '__main__':
    unittest.main()
