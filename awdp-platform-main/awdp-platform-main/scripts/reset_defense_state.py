from app import create_app, db
from app.models import Defense

app = create_app()

def main(def_id=1):
    with app.app_context():
        d = Defense.query.get(def_id)
        if not d:
            print('no defense')
            return
        d.status = 'uploaded'
        d.result = None
        db.session.commit()
        print('reset defense', d.id)

if __name__ == '__main__':
    main()
