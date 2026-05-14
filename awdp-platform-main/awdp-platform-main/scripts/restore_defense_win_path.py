from app import create_app, db
from app.models import Defense
import os

app = create_app()

def main(def_id=1):
    with app.app_context():
        d = Defense.query.get(def_id)
        if not d:
            print('no defense')
            return
        win_path = os.path.join(os.getcwd(), 'uploads', 'def_sample.tar.gz')
        d.filename = win_path
        db.session.commit()
        print('restored to', d.filename)

if __name__ == '__main__':
    main()
