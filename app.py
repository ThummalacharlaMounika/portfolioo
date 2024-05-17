from flask import Flask,flash,redirect,render_template,url_for,request,jsonify,session,abort
from flask_session import Session
from werkzeug.utils import secure_filename
#from flask_mysqldb import MySQL
from datetime import date
from datetime import datetime
from sdmail import sendmail
from tokenreset import token
from stoken1 import token1
from flask import send_file
from mysql.connector import OperationalError
import mysql.connector
import os
from itsdangerous import URLSafeTimedSerializer
from key import *
app=Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static')
app.secret_key='hello'
app.config['SESSION_TYPE'] = 'filesystem'
# app.config['MYSQL_HOST'] ='localhost'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD']='admin'
# app.config['MYSQL_DB']='personal_portfolio'
mydb=mysql.connector.connect(host='localhost',user='root',password='Admin',db='subbu')
#mysql=MySQL(app)
Session(app)
@app.route('/home')
def home():
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select * from post')
    data=cursor.fetchall()
    cursor.close()
    return render_template('home.html',data=data)
#=========================================Users login and register
@app.route('/ulogin',methods=['GET','POST'])
def ulogin():
    if session.get('user'):
        return redirect(url_for('users_dashboard'))
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('SELECT count(*) from users where username=%s and password=%s',[username,password])
        count=cursor.fetchone()[0]
        if count==1:
            session['user']=username
            if not session.get(username):
                session[username]={}
            return redirect(url_for("users_dashboard"))
        else:
            flash('Invalid username or password')
            return render_template('userlogin.html')
    return render_template('userlogin.html')

@app.route('/uregistration',methods=['GET','POST'])
def uregistration():
    if request.method=='POST':
        username = request.form['username']
        password=request.form['password']
        email=request.form['email']
        
        
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from users where username=%s',[username])
        count=cursor.fetchone()[0]
        cursor.execute('select count(*) from users where email=%s',[email])
        count1=cursor.fetchone()[0]
        cursor.close()
        if count==1:
            flash('username already in use')
            return render_template('userregister.html')
        elif count1==1:
            flash('Email already in use')
            return render_template('userregister.html')
        
        data={'username':username,'email':email,'password':password}
        subject='Email Confirmation'
        body=f"Thanks for signing up\n\nfollow this link for further steps-{url_for('uconfirm',token=token(data,salt),_external=True)}"
        sendmail(to=email,subject=subject,body=body)
        flash('Confirmation link sent to mail')
        return redirect(url_for('uregistration'))
    
    return render_template('userregister.html')
@app.route('/uconfirm/<token>')
def uconfirm(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        data=serializer.loads(token,salt=salt,max_age=180)
    except Exception as e:
      
        return 'Link Expired register again'
    else:
        cursor=mydb.cursor(buffered=True)
        id1=data['username']
        cursor.execute('select count(*) from users where username=%s',[id1])
        count=cursor.fetchone()[0]
        if count==1:
            cursor.close()
            flash('You are already registerterd!')
            return redirect(url_for('ulogin'))
        else:
            cursor.execute('INSERT INTO users (username, password,email) VALUES (%s,%s,%s)',[data['username'], data['password'], data['email']])

            mydb.commit()
            cursor.close()
            flash('Details registered!')
            return redirect(url_for('ulogin'))
@app.route('/forget',methods=['GET','POST'])
def forgot():
    if request.method=='POST':
        id1=request.form['id1']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from users where username=%s',[id1])
        count=cursor.fetchone()[0]
        cursor.close()
        if count==1:
            cursor=mydb.cursor(buffered=True)

            cursor.execute('SELECT email  from users where username=%s',[id1])
            email=cursor.fetchone()[0]
            cursor.close()
            subject='Forget Password'
            confirm_link=url_for('reset',token=token(id1,salt=salt2),_external=True)
            body=f"Use this link to reset your password-\n\n{confirm_link}"
            sendmail(to=email,body=body,subject=subject)
            flash('Reset link sent check your email')
            return redirect(url_for('ulogin'))
        else:
            flash('Invalid email id')
            return render_template('forgot.html')
    return render_template('forgot.html')

()
@app.route('/reset/<token>',methods=['GET','POST'])
def reset(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        id1=serializer.loads(token,salt=salt2,max_age=180)
    except:
        abort(404,'Link Expired')
    else:
        if request.method=='POST':
            newpassword=request.form['npassword']
            confirmpassword=request.form['cpassword']
            if newpassword==confirmpassword:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('update  users set password=%s where username=%s',[newpassword,id1])
                mydb.commit()
                flash('Reset Successful')
                return redirect(url_for('ulogin'))
            else:
                flash('Passwords mismatched')
                return render_template('newpassword.html')
        return render_template('newpassword.html')
@app.route('/ulogout')
def ulogout():
    if session.get('user'):
        session.pop('user')
        flash('Successfully loged out')
        return redirect(url_for('ulogin'))
    
    return redirect(url_for('ulogin'))

@app.route('/users_dashboard',methods=['GET','POST'])
def users_dashboard():
    if session.get('user'):

        

        return render_template('users_dashboard.html')
    else:
        return redirect(url_for('ulogin'))
import random
def genotp():
    u_c=[chr(i) for i in range(ord('A'),ord('Z')+1)]
    l_c=[chr(i) for i in range(ord('a'),ord('z')+1)]
    otp=''
    for i in range(3):
        otp+=random.choice(u_c)
        otp+=str(random.randint(0,9))
        otp+=random.choice(l_c)
    return otp
@app.route('/submit_form', methods=['GET', 'POST'])
def submit_form():
    if session.get('user'):
        if request.method == 'POST':
            id1_pic = genotp()
            introduction = request.form['introduction']
            phnumber = request.form['phnumber']
            email = request.form['email']
            about = request.form['about']
            profile = request.form['profile']
            skills = request.form['skills']
            languages = request.form['languages']
            education = request.form['education']
            project_title = request.form['project_title']
            desc = request.form['project_description']
            image = request.files['image']
            link = request.form['link']
            resume = request.files['resume']
            
            # Generate secure filenames for image and resume
            image_filename = secure_filename(image.filename)
            resume_filename = secure_filename(resume.filename)
            
            # Generate unique filenames
        
            
            cur = mydb.cursor(buffered=True)
            cur.execute('select count(*) from user_data where username=%s', [session['user'], ])
            u = cur.fetchone()[0]
            if u == 1:
                flash('You already created a portfolio account, please view once')
                return redirect(url_for('view_portfolio'))
            else:
                cur.execute('INSERT INTO user_data (introduction, username, phnumber, email, about, profile, skills, '
                            'languages, education, project_title, project_description, image, link, resume_file) '
                            'VALUES (%s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                            (introduction, session['user'], phnumber, email, about, profile, skills, languages,
                             education, project_title, desc,image_filename, link, resume_filename))
                
                # Save files to the static folder
                static_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static')
                image.save(os.path.join(static_folder, image_filename))
                resume.save(os.path.join(static_folder, resume_filename))
                
                mydb.commit()
                cur.close()
                
                flash('Form submitted successfully! Now select the template', 'success')
                return redirect(url_for('submit_form'))  # Redirect to the homepage or any other page
        return render_template('enteruserportfolio.html')
    else:
        return redirect(url_for('ulogin'))
@app.route('/view_portfolio',methods=['GET','POST'])
def view_portfolio():
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from user_data where username=%s',[session.get('user'),])
        data=cursor.fetchone()
        return render_template('template2.html',data=data)
    return redirect(url_for('ulogin'))
@app.route('/deleteportfolio')
def deleteportfolio():
    if session.get('user'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('SELECT image FROM user_data WHERE username = %s', [session['user'],])
        image_filename = cursor.fetchone()[0]  # Get the image filename
        #print('==================================',image_filename)
      
        path_to_image = os.path.join(app.config['UPLOAD_FOLDER'], image_filename+'.jpg')
        #print("=======================================",path_to_image)
        if os.path.exists(path_to_image):
            #print('=================================,the path exists')
            os.remove(path_to_image)  # Delete the image file from the static folder
        cursor.execute('DELETE FROM user_data WHERE username = %s', [session['user']])
        mydb.commit()
        cursor.close()
        flash('Your portfolio has been deleted successfully.', 'success')
        return redirect(url_for('view_portfolio'))
    return redirect(url_for('ulogin'))
#======================= update portfolio
@app.route('/update_portfolio',methods=['GET','POST'])
def update_portfolio():
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from user_data where username=%s',[session['user'],])
        i = cursor.fetchall()
        
        #print('===================================',i)
        if request.method == 'POST':
            id1_pic=genotp()
            introduction = request.form['introduction']
            phnumber = request.form['phnumber']
            email = request.form['email']
            about = request.form['about']
            profile = request.form['profile']
            skills = request.form['skills']
            languages = request.form['languages']
            education = request.form['education']
            project_title = request.form['project_title']
            project_description = request.form['project_description']
            image = request.files['image']
            img=image.filename
            link = request.form['link']
            resume = request.files['resume']
            filename=resume.filename
            print(filename)
            cursor.execute('SELECT image FROM user_data WHERE username = %s', [session['user'],])
            image_filename = cursor.fetchone()[0]  # Get the image filename
            #print('==================================',image_filename)
        
            path_to_image = os.path.join(app.config['UPLOAD_FOLDER'], img)
            path_to_resume = os.path.join(app.config['UPLOAD_FOLDER'],filename)
            #print("=======================================",path_to_image)
            if os.path.exists(path_to_image):
                #print('=================================,the path exists')
                os.remove(path_to_image)  # Delete the image file from the static folder
            #print('================================',data)
            if os.path.exists(path_to_image):
                os.remove(path_to_resume)
            cursor.execute('''UPDATE user_data SET introduction=%s, phnumber=%s, email=%s, about=%s, profile=%s, 
                              skills=%s, languages=%s, education=%s, project_title=%s, project_description=%s, 
                              image=%s, link=%s, resume_file=%s WHERE username=%s''',
                           (introduction, phnumber, email, about, profile, skills, languages, education,
                            project_title, project_description, id1_pic, link, filename, session['user']))
            mydb.commit()
            
            path=os.path.join(os.path.abspath(os.path.dirname(__file__)),'static')
            if not os.path.exists(path):
                os.makedirs(path,exist_ok=True)
        
            image.save(os.path.join(path, filename))
            flash('Portfolio updated successfully', 'success')
            return redirect(url_for('users_dashboard'))
        
        return render_template('update_portfolio.html',i=i)
    return redirect(url_for('ulogin'))
@app.route('/view_resume/<username>')
def view_resume(username):
    cursor = mydb.cursor(buffered=True)
    cursor.execute('SELECT resume_file FROM user_data WHERE username = %s', [username])
    resume_data = cursor.fetchone()[0]
    print(resume_data)
    cursor.close()

    if resume_data:
        # Construct the path to the resume file
        path_to_resume = os.path.join(app.config['UPLOAD_FOLDER'], resume_data)

        # Check if the file exists
        if os.path.exists(path_to_resume):
            # Attempt to send the file for download
            try:
                return send_file(path_to_resume, as_attachment=True)
            except Exception as e:
                # Log the error and inform the user
                app.logger.error(f"Error sending resume file: {e}")
                flash('Error sending resume file. Please try again later.')
                return redirect(url_for('users_dashboard'))
        else:
            flash('Resume not found.')
            return redirect(url_for('users_dashboard'))
    else:
        flash('Resume not found.')
        return redirect(url_for('users_dashboard'))
#creating blogs
@app.route('/createpost', methods=['GET','POST'])
def createpost():
    if session.get('user'):
        if request.method=='POST':
            image=request.files['image']
            descp=request.form['descp']
            # filename=image.filename.split('.')[-1]
            # if filename!='jpg':
            #     flash('wrong input file')
            #     return render_template('createpost.html')
            caption=request.form['caption']
            cursor=mydb.cursor(buffered=True)
            username=session.get('user')
            pid=genotp()
            #path=r"E:\personal_portfolio\static"
            filename=pid+'.jpg'
            path=os.path.join(os.path.abspath(os.path.dirname(__file__)),'static')
            if not os.path.exists(path):
                os.makedirs(path,exist_ok=True) 
           
                
          
            image.save(os.path.join(path, filename))
            cursor.execute('insert into post(pid,username,caption,descp,images) values(%s,%s,%s,%s,%s)',[pid,username,caption,descp,pid])
            mydb.commit()
            cursor.close() 
            flash(f'{username} added your post successfully')
            return redirect(url_for('viewposts'))
        return render_template('createpost.html')
    else:
        return redirect(url_for('login'))

@app.route('/viewposts')
def viewposts():
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from post where username=%s',[session['user']])
        data=cursor.fetchall()
        return render_template('viewposts.html',data=data)   
    else:
        return redirect(url_for('ulogin'))
    

@app.route('/deletepost/<pid>')
def deletepost(pid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('SELECT images FROM post WHERE pid = %s', [pid])
        image_filename = cursor.fetchone()[0]  # Get the image filename
        #print('==================================',image_filename)
      
        path_to_image = os.path.join(app.config['UPLOAD_FOLDER'], image_filename+'.jpg')
        #print("=======================================",path_to_image)
        if os.path.exists(path_to_image):
            #print('=================================,the path exists')
            os.remove(path_to_image)  # Delete the image file from the static folder
        cursor.execute('delete from post where pid=%s',[pid])
        mydb.commit()
        cursor.close
        flash('post deleted successfully')
        return redirect(url_for('viewposts'))
    return redirect(url_for('ulogin'))
#===================view the portfolio based on the selected templates
def selecttemplate():
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from user_data where username=%s',[session.get('user'),])
        data=cursor.fetchone()
        return data
 #=======================select design 1 template
@app.route('/design1/<name>')
def design1(name):
    print(name)
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from post where username=%s',[session['user']])
        data=cursor.fetchall()
        print(data,111)
        if data:
            username=session['user']
            data = selecttemplate()
            return render_template(f'customizetemplates/{name}.html',i=data,username=username)
        else:
            flash(' please enter the data ')
            return redirect(url_for('submit_form'))


    return redirect(url_for('ulogin'))

#============================== share the portfolio
@app.route('/design/<name>/<username>')
def design(name,username):
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select * from user_data where username=%s',[username])
    data=cursor.fetchone()
    # if data:
    
    
    return render_template(f'customizetemplates/{name}.html',i=data,username=username)
    # else:
    #     flash(' please enter the data ')
    #     return redirect(url_for('submit_form'))

#========================================= contact

@app.route('/contact_form',methods=['GET','POST'])
def contact_form():
    if request.method=="POST":
        ename = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        message = request.form['message']
        cursor=mydb.cursor(buffered=True)
        cursor.execute("INSERT INTO contact_form(user_id,name, email, phone_number, message) VALUES (%s, %s, %s, %s, %s)", (ename, ename, email, phone, message))
        mydb.commit()        #mydb.commit()
        flash('your message submitted sucessfully')
        return render_template('contact_form.html') 
        
    return render_template('contact_form.html')
#===================== read contact us
@app.route('/read_contact')
def read_contact():
    if session.get('user'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('select * from contact_form where user_id=%s',[session['user']])
        data = cursor.fetchall()
        return render_template('readcontactus.html',queries = data) 
    return redirect(url_for('ulogin'))
@app.route('/about')
def about():

    cursor=mydb.cursor(buffered=True)
    cursor.execute('select * from post')
    data=cursor.fetchall()
    cursor.close()
    return render_template('about.html',data=data)

@app.route('/')
def page():

    return render_template('blogs.html')

@app.route('/viewmore/<pid>')
def viewmore(pid):
    
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select *  from post where pid=%s',[pid])
    mydb.commit()
    return redirect(url_for('page'))
app.run(use_reloader=True,debug=True)