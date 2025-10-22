@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))