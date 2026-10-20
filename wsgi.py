import os
from waitress import serve
from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    threads = int(os.environ.get('WAITRESS_THREADS', 8))
    print(f"==================================================================")
    print(f"  Apex Student Attendance Management System (Production WSGI)")
    print(f"  Serving via Waitress on http://{host}:{port}")
    print(f"  Worker Threads: {threads}")
    print(f"  Data Storage: Microsoft Excel (OpenPyXL / Pandas)")
    print(f"==================================================================")
    serve(app, host=host, port=port, threads=threads)
