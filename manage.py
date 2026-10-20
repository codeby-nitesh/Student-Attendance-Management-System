import sys
import argparse
from werkzeug.security import generate_password_hash
from services.excel_service import ExcelService
from services.auth_service import AuthService
from services.backup_service import BackupService

def init_db():
    print("[*] Initializing Excel workbooks in data/ directory...")
    ExcelService.init_all_files()
    print("[+] All Excel workbooks initialized successfully!")

def create_admin(username, password, full_name, email):
    init_db()
    success, msg = AuthService.create_user(username, password, full_name, email, role='Admin', status='Active')
    if success:
        print(f"[+] Administrator '{username}' created successfully!")
    else:
        print(f"[-] Error: {msg}")

def backup_all():
    print("[*] Triggering full workbook backup...")
    success, msg = BackupService.create_backup_now()
    print(f"[+] {msg}")

def check_integrity():
    print("[*] Checking Excel database health...")
    stats = BackupService.get_workbook_stats()
    for s in stats:
        print(f"  - {s['filename']:20} | Rows: {s['row_count']:5} | Size: {s['size_kb']:6} KB | Status: {s['status']}")
    print("[+] Health check complete.")

def main():
    parser = argparse.ArgumentParser(description="Apex Attendance System CLI Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # init
    subparsers.add_parser("init", help="Initialize all Excel workbooks")

    # create-admin
    admin_parser = subparsers.add_parser("create-admin", help="Create an administrator account")
    admin_parser.add_argument("--username", required=True, help="Username")
    admin_parser.add_argument("--password", required=True, help="Password")
    admin_parser.add_argument("--name", default="System Administrator", help="Full name")
    admin_parser.add_argument("--email", default="admin@example.com", help="Email address")

    # backup
    subparsers.add_parser("backup", help="Create backups of all workbooks")

    # check
    subparsers.add_parser("check", help="Verify Excel workbooks integrity")

    args = parser.parse_args()

    if args.command == "init":
        init_db()
    elif args.command == "create-admin":
        create_admin(args.username, args.password, args.name, args.email)
    elif args.command == "backup":
        backup_all()
    elif args.command == "check":
        check_integrity()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
