
import sys
from getpass import GetPassWarning
import warnings

from app import app, db, Admin, init_db


def read_password(prompt):
    """Read password visibly for reliable VS Code terminal input."""
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print("\nPassword input cancelled.")
        raise SystemExit(1)


def main():
    with app.app_context():
        init_db()

        if Admin.query.count() > 0:
            print(
                "An administrator already exists. "
                "Use the dashboard password-change page."
            )
            return

        username = input("New admin username: ").strip()

        if not username or len(username) > 80:
            print("Username must be between 1 and 80 characters.")
            return

        while True:
            password = read_password(
                "New admin password (minimum 12 characters): "
            )

            if len(password) < 12:
                print("Password must be at least 12 characters.")
                continue

            confirm_password = read_password("Confirm password: ")

            if password != confirm_password:
                print("Passwords do not match. Try again.")
                continue

            break

        admin = Admin(username=username)
        admin.set_password(password)

        try:
            db.session.add(admin)
            db.session.commit()
            print("\nAdmin created successfully!")
            print("You can now log in to your dashboard.")

        except Exception as error:
            db.session.rollback()
            print(f"Could not create admin: {error}")
            raise SystemExit(1)


if __name__ == "__main__":
    main()
