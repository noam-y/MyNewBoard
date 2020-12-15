from flask import Flask, render_template, url_for, redirect, request, session
import peewee
from db_creator import User, Quote, Board, QuotesBoards, db as database
import config
from playhouse.shortcuts import model_to_dict

app = Flask(__name__)
app.config.from_pyfile('config.py')
app.secret_key = 'Nothing to say except Efi koosit'


# This hook ensures that a connection is opened to handle any queries
# generated by the request.
@app.before_request
def _db_connect():
    database.connect()


# This hook ensures that the connection is closed when we've finished
# processing the request.
@app.teardown_request
def _db_close(exc):
    if not database.is_closed():
        database.close()


@app.route('/')
def homepage():
    return render_template("homepage.html", islogged='user_id' in session)


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # return f'answer is {User.select().where(User.username == username).exists()}'
        if User.select().where(User.username == username).exists():
            # handles case where username is already taken
            return render_template("register.html", message='username already taken. try again.', islogged='user_id' in session)
        elif len(password) <= 8:
            return render_template("register.html", message='Your password must be at least 8 characters-try again', islogged='user_id' in session)
        elif len(username) <= 7:
            return render_template("register.html", message='Your name must be at least 7 characters-try again', islogged='user_id' in session)

        else:
            if (password == request.form.get('confirm-password')):
                #checks that password was typed correctrly
                newuser = User.create(username=username, password=password)
                newuser.save()
                session['user_id'] = User.select().where(
                    User.username == username).get().id
                return redirect(url_for('quote', islogged='user_id' in session))
            else:
                 return render_template("register.html", message='passwords not matching- try again!', islogged='user_id' in session)

    else:
        return render_template("register.html", message='', islogged='user_id' in session)


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.select().where((User.username == username) & (User.password == password))
        if not user.exists():
            return render_template("login.html", message='wrong username/password- try again!', islogged='user_id' in session)
        else:
            session['user_id'] = user.get().id
            return redirect(url_for('quote'))

    else:
        return render_template("login.html", message='', islogged='user_id' in session)


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))


#######################################################################################################################
##############################        DISPLAYING QUOTES AND BOARDS                 ####################################
#######################################################################################################################

@app.route('/myquotes')
def my_quotes():
    if 'user_id' in session:
        my_quotes = User.select(peewee.fn.ARRAY_AGG(User.username).alias('username'), Quote.description,peewee.fn.ARRAY_TO_STRING(peewee.fn.ARRAY_AGG(Board.title),', ').alias('title')).join(Quote).join(QuotesBoards, on=(QuotesBoards.quote_id == Quote.id)).join(Board).where(Quote.user_id == User.get_by_id(session['user_id'])).group_by(User.username,Quote.description)
        my_quotes = list(my_quotes.dicts())
        return render_template("quote_display.html", quotes=my_quotes, user=session['user_id'], islogged='user_id' in session,display='user')
    else:
        return render_template("quote_display.html", islogged=False)

@app.route('/board')
def watch_board():

    if 'user_id' in session:
        required_board_id = 1
        board_quotes = QuotesBoards.select(Quote.description,User.username).join(Quote).join(User).where(QuotesBoards.board_id == required_board_id)
        board_quotes = list(board_quotes.dicts())
        return render_template("quote_display.html",boards=get_boards(), quotes=board_quotes, user=session['user_id'], islogged='user_id' in session, display='board')
    else:
        return render_template("quote_display.html", islogged=False)

#######################################################################################################################
##############################        CREATING BOARDS AND QUOTES                   ####################################
#######################################################################################################################


@app.route('/addquote', methods=['POST', 'GET'])
def quote():

    if 'user_id' not in session:
        return render_template("add-quote.html", islogged=False)

    else:
        user = User.get_by_id(int(session['user_id']))
        username = user.username
        if request.method == 'POST':
            quote = request.form.get('quote')
            if Quote.select().where(Quote.description == quote).exists():
                # handles case that quote already exists in the system.
                return render_template("add-quote.html", username=username, boards=get_boards(), message="the quote you entered already exists- try again.", islogged='user_id' in session)
            elif len(quote) < 15:
                return render_template("add-quote.html", username=username, boards=get_boards(), message="the quote you entered is too short- try again.", islogged='user_id' in session)
            else:
                try:
                    new_quote = Quote.create(
                    description=quote, user_id=session['user_id'])
                    new_quote.save()
                except peewee.DataError:
                    database.rollback()
                    return render_template("add-quote.html", username=username, boards=get_boards(), message='quote is too long- try adding a shorter quote.', islogged='user_id' in session)
                quote_id = Quote.select().where(Quote.description == quote).get().id
                boards_matching = request.form.getlist('boards')
                for b in boards_matching:
                    newlink = QuotesBoards.create(
                        quote_id=quote_id, board_id=b)
                    newlink.save()
                return render_template("add-quote.html", username=username, boards=get_boards(), message=f'{username}, your quote was added to our main gallery.', islogged='user_id' in session)
        else:
            return render_template("add-quote.html", username=username, boards=get_boards(), message='', islogged='user_id' in session)





@app.route('/createboard', methods=['POST', 'GET'])
def new_board():
    if 'user_id' not in session:
        return render_template("add-quote.html", islogged=False)
    else:
        user = User.get_by_id(int(session['user_id']))
        username = user.username
        if request.method == 'POST':
            title = request.form.get('title')
            description = request.form.get('description')
            if Board.select().where(Board.title == title).exists():
                # handles case when board with this title already exists.
                return render_template("add-board.html", username=username, quotes=get_quotes(), message='board with this title already exists.', islogged='user_id' in session)
            elif (len(title) < 3):
                return render_template("add-board.html", username=username, quotes=get_quotes(), message='title of board must be at least 3 characters long..', islogged='user_id' in session)
            else:
                new_board = Board.create(title=title, description=description)
                new_board.save()
                # adding the quotes related to the board
                board_id = Board.select().where(Board.title == title).get().id
                quotes_in_board = request.form.getlist('quotes')
                # return f'number of qoutes in board- {quotes_in_board}'
                for q in quotes_in_board:
                    newlink = QuotesBoards.create(
                        quote_id=q, board_id=board_id)
                    newlink.save()
                return render_template("add-board.html", username=username, quotes=get_quotes(), message='Board created Successfuly!', islogged='user_id' in session)
        else:
            return render_template("add-board.html", username=username, quotes=get_quotes(), message='', islogged='user_id' in session)


def get_quotes():
    all_quotes = Quote.select()
    return all_quotes


def get_boards():
    all_boards = Board.select()
    return all_boards


if __name__ == "__main__":
    app.run(debug=True)
 ###########################################################################################################################################
 ############################################## VALIDATION
 ###########################################################################################################################################

@app.route('/validator')
def validator():
    invalid_user_ids = User.select(User.id).where(peewee.fn.length(User.username) < 6 ^ peewee.fn.length(User.password) < 8)
    new_q = Quote.delete().where(Quote.user_id.in_(invalid_user_ids))
    new_q.execute()
    q = User.delete().where(peewee.fn.length(User.username) < 6 ^ peewee.fn.length(User.password) < 8)
    q.execute()
    q = Quote.delete().where(peewee.fn.length(Quote.description) < 15)
    q.execute()
    return 'removed bad users and bad quotes.'