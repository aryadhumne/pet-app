content = open('files/models.py').read()
old = 'created_at = db.Column(db.DateTime, default=datetime.utcnow)'
new = 'created_at = db.Column(db.DateTime, default=datetime.utcnow)\n    photo = db.Column(db.String(200), nullable=True, default=None)'
open('files/models.py', 'w').write(content.replace(old, new))
print('Done! photo column added.')
print('photo' in open('files/models.py').read())