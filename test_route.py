from app import app, db

app.app_context().push()

with app.test_client() as c:
    with c.session_transaction() as sess:
        sess['user_id'] = 1
    r = c.get('/my-appointments')
    print(r.status_code)
    print(r.data.decode())