#!/usr/bin/python

import configparser
import psycopg2 as PostgreSQL
import sys

from GooglePlacesAPI import GooglePlaces
from QueryDatabase import QueryDB


__all__ = ['ContactManagerDB', 'ConfigurationErrorDB', 'ContactManagerErrorDB']
__version__ = 1.0


class ConfigurationErrorDB(Exception):
    """
    Exception for database configuration errors.
    """

    def __init__(self, msg, original_exception=None):
        if original_exception is not None:
            msg += ": {}".format(original_exception)
        super(ConfigurationErrorDB, self).__init__(msg)
        self.original_exception = original_exception


class ContactManagerErrorDB(PostgreSQL.Error):
    """
    Exception for database related errors.
    """
    pass


class ContactManagerDB(object):
    """
    Class for the contact manager database interface.
    """

    def __init__(self):
        """
        Initializes database interface connection.
        """
        self._db_params = self._configuration_database()

    def __str__(self):
        """
        Returns a string representation of database connection.
        """
        db_params = {
            'classname': self.__class__.__name__,
            'host': self._db_params['host'],
            'port': self._db_params['port'],
            'dbname': self._db_params['dbname'],
            'user': 'X' * len(self._db_params['user']),
            'password': 'X' * len(self._db_params['password']),
        }
        return '<{classname}: host={host}, port={port}, dbname={dbname}, \
                user={user}, password={password}>'.format(**db_params)

    def _configuration_database(self, filename='contact_manager.ini', section='postgresql'):
        """
        Parses database configuration.
        """
        parser = configparser.ConfigParser()
        parser.read(filename)
        db_params = {}
        if parser.has_section(section):
            params = parser.items(section)
            for param in params:
                db_params[param[0]] = param[1]
        else:
            msg = 'Section {} not found in {} filename'.format(section, filename)
            raise ConfigurationErrorDB(msg)
        return db_params

    def _connection_database(self, db=None):
        """
        Establishes connection with database.
        """
        db = PostgreSQL.connect(**self._db_params)
        cursor = db.cursor()
        return db, cursor

    def _close_connection_database(self, db, cursor):
        """
        Closes connection with database.
        """
        if db is not None:
            cursor.close()
            db.close()

    def check_database(self):
        """
        Checks database while starting contacts manager.
        """
        try:
            print 'Attempting connection with PostgreSQL database...'
            db, cursor = self._connection_database()
            cursor.execute(QueryDB.queries_dict()[SQL_CHECK])
            db_version = cursor.fetchone()
        except ContactManagerErrorDB as msg:
            print('Connection failed: ', msg, sep='')
        finally:
            self._close_connection_database(db, cursor)
        print('Connection to database successfull.')
        return db_version

    def check_contact_table(self):
        """
        Check contacts table and creates it if does not exit.
        """
        try:
            db, cursor = self._connection_database()
            cursor.execute(QueryDB.queries_dict()[SQL_CREATE])
            db.commit()
        except ContactManagerErrorDB as msg:
            print('Error checking table of contacts: ', msg, sep='')
        finally:
            self._close_connection_database(db, cursor)

    def _get_registry_input(self, registry, contact_id=None):
        """
        Fetches data input and validates it calling data
        validator class.
        """
        #TODO
        pass

    def insert_new_registry(self, registry):
        """
        Inserts new contact registry in the database.
        """
        input_data = self._get_registry_input(registry)
        try:
            db, cursor = self._connection_database()
            cursor.execute(QueryDB.queries_dict()[SQL_INSERT], input_data)
            contact_id = cursor.fetchone()[0]
            db.commit()
        except ContactManagerErrorDB as msg:
            print('Error inserting new registry into database: ', msg, sep='')
        finally:
            self._close_connection_database(db, cursor)
        return contact_id

    def update_registry(self, registry, contact_id):
        """
        Modifies contact registry already existing in
        the database.
        """
        input_data = self._get_registry_input(registry, contact_id)
        try:
            db, cursor = self._connection_database()
            cursor.execute(QueryDB.queries_dict()[SQL_UPDATE], input_data)
            updated_rows = cursor.rowcount
            db.commit()
        except ContactManagerErrorDB as msg:
            print('Error updating registry into database: ', msg, sep='')
        finally:
            self._close_connection_database(db, cursor)
        if updated_rows:
            print('Contact registry successfully updated.')
            return updated_rows

    def list_selected_contacts(self):
        """
        Lists all registered contacts in database.
        """
        try:
            db, cursor = self._connection_database()
            cursor.execute(QueryDB.queries_dict()[SQL_SELECT_ALL])
            rows = cursor.fetchall()
        except ContactManagerErrorDB as msg:
            print('Error listing all registered contacts: ', msg, sep='')
        finally:
            self._close_connection_database(db, cursor)
        return rows

    def query_registry(self, registry):
        """
        Queries registered contacts in database.
        """
        name = registry.get('Name')
        direction = registry.get('Direction')
        email = registry.get('Email')

        rows = []
        try:
            db, cursor = self._connection_database()
            sql = self._construct_query(name, direction, email)
            if sql is not None:
                cursor.execute(sql)
                rows = cursor.fetchall()
        except ContactManagerErrorDB as msg:
            print('Error selecting registry: ', msg, sep='')
        finally:
            self._close_connection_database(db, cursor)
        return rows

    def _construct_query(self, name, direction, email):
        """
        Constructs the query based on the filter conditions.
        """
        # Base query.
        sql = QueryDB.queries_dict()[SQL_SELECT]
        conditions = self._query_conditions(name, direction, email)
        # Construct the query conditions.
        if conditions:
            for count, condition in enumerate(conditions, start=1):
                sql += condition
                if count < len(conditions):
                    sql += "AND"
            sql += QueryDB.queries_dict()[SQL_SORT]
            return sql
        return None

    def _query_conditions(self, name, post_town_country, email):
        """
        Contructs query conditions.
        """
        conditions = []
        if name:
            cond_name = " Name = '{}' ".format(name)
            conditions.append(cond_name)
        if direction:
            direction = '%' + direction + '%'
            cond_direction = " Direction LIKE '{}' ".format(direction)
            conditions.append(cond_direction)
        if email:
            cond_email = " Email = '{}' ".format(email)
            conditions.append(cond_email)
        return conditions

    def delete_registry(self, contact_id):
        """
        Deletes contact registry from database.
        """
        try:
            db, cursor = self._connection_database()
            cursor.execute(QueryDB.queries_dict()[SQL_DELETE], (contact_id,))
            deleted_rows = cursor.rowcount
            db.commit()
        except ContactManagerErrorDB as msg:
            print('Error deleting registry from database: ', msg, sep='')
        finally:
            self._close_connection_database(db, cursor)
        if deleted_rows:
            print('Contact registry successfully deleted.')
            return deleted_rows
