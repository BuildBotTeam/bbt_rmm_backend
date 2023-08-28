db = db.getSiblingDB('db');
db.createUser(
    {
        user: "admin",
        pwd: "admin",
        roles: [
            {
                role: "readWrite",
                db: "db"
            }
        ]
    }
);
db.createCollection('users');
db.users.createIndex({"username": 1}, {unique: true})
db.users.insert({username: 'admin'})
