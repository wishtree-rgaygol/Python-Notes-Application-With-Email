from flask import Flask
from flask_mail import Mail,Message
app=Flask(__name__)
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT']=465
app.config['MAIL_USERNAME']='ravigaygol90@gmail.com'
app.config['MAIL_PASSWORD']='07258218418'
app.config['MAIL_USE_TLS']=False
app.config['MAIL_USE_SSL']=True

users=[{'name':'ravi','email':'ravigaygol90@gmail.com'},{'name':'pooja','email':'poojagaygol94@gmail.com'},{'name':'mayuri','email':'mayurishelke1608@gmail.com'}]
mail=Mail(app)
@app.route('/')
def index():
    with mail.connect()as con:
        for user in users:
            message="hey %s" %user['name'] +" ,i sent you the bulk mail for testing..my first bulk mail by using Flask"
            msgs=Message(recipients=[user['email']],body=message,subject='hello',sender='Ravi Gaygol')
            con.send(msgs)
        return "mail Sent"
if __name__ == '__main__':
    app.run(debug=True)