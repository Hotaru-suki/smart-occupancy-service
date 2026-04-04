import getpass

from app.security.passwords import hash_password


def main():
    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm : ")
    if password != confirm:
        raise SystemExit("Passwords do not match.")

    print(hash_password(password))


if __name__ == "__main__":
    main()
