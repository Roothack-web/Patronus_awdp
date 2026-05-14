from app import create_app, db
from app.models import Defense, User
import sys

app = create_app()

def main(def_id=1):
    with app.app_context():
        d = Defense.query.get(def_id)
        if not d:
            print('no defense')
            return
        print('Defense:', d.id, d.status, d.result)
        u = User.query.get(d.user_id)
        if u:
            print('User:', u.id, u.username, 'score=', u.score)

if __name__ == '__main__':
    arg = 1
    if len(sys.argv) >= 2:
        try:
            arg = int(sys.argv[1])
        except Exception:
            arg = 1
    main(arg)
