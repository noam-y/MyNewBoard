#!/usr/bin/env python3

from peewee import PostgresqlDatabase, CharField, IntegerField,PrimaryKeyField,ForeignKeyField,Model
import datetime
import os

#db = peewee.SqliteDatabase('inspire_app.db')
#db = PostgresqlDatabase('MyBoard.db',password='postgres')



db = PostgresqlDatabase(
    os.environ['DATABASE'],
    user=os.environ['POST_USER'],
    password=os.environ['POST_PASS'],
    host=os.environ['POST_HOST'],
    port=os.environ['POST_PORT'],
)
#heroku deploy settings


class BaseModel(Model):

    class Meta:

        database = db


class User(BaseModel):

    username = CharField(unique=True)
    password = CharField()

    class Meta:

        db_table = 'users'


class Board(BaseModel):

    title = CharField(unique=True)
    description = CharField()

    class Meta:

        db_table = 'boards'


class Quote(BaseModel):

    user_id = ForeignKeyField(User)
    description = CharField(unique=True)
    

    class Meta:

        db_table = 'quotes'

class QuotesBoards(BaseModel):

    board_id = ForeignKeyField(Board)
    quote_id = ForeignKeyField(Quote)

    class Meta:

        db_table = 'quotes_boards'



tables = [User,Board,Quote,QuotesBoards]
db.create_tables(tables)