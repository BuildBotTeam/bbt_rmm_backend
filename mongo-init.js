var rand = function () {
    return Math.random().toString(36).substr(2);
};

var token = function () {
    return rand() + rand() + rand();
};

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
db.mikrotik_routers.createIndex({"host": 1}, {unique: true})
const usernames = process.env.DB_ADMIN_USERNAME.toString().split(' ')
const emails = process.env.DB_ADMIN_EMAIL.toString().split(' ')
const passwords = process.env.DB_ADMIN_PASSWORD.toString().split(' ')
for (let i = 0; i < usernames.length; i++) {
    db.users.insert(
        {
            username: usernames[i],
            password: passwords[i],
            email: emails[i],
            active: true,
            admin: true,
            token: token()
        }
    )
}
