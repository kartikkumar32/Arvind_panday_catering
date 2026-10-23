import os
import tempfile
import unittest
from app import app, db, Admin, init_db

class CateringAppTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        app.config.update(
            TESTING=True,
            WTF_CSRF_ENABLED=False,
            SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(self.temp_dir.name, "test.db"),
            SECRET_KEY="test-secret-key",
            UPLOAD_FOLDER=self.temp_dir.name,
        )
        with app.app_context():
            db.drop_all()
            db.create_all()
            admin = Admin(username="testadmin")
            admin.set_password("test-password-long")
            db.session.add(admin)
            db.session.commit()
        self.client = app.test_client()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()
        self.temp_dir.cleanup()

    def test_public_pages(self):
        for path in ["/", "/about", "/services", "/certifications", "/branches", "/team", "/contact"]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)

    def test_admin_requires_login(self):
        response = self.client.get("/admin")
        self.assertIn(response.status_code, (302, 401))

    def test_admin_login(self):
        response = self.client.post("/admin/login", data={"username": "testadmin", "password": "test-password-long"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Overview", response.data)

if __name__ == "__main__":
    unittest.main()
