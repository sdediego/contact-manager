#!/usr/bin/python

__all__ = ['QueryDB']
__version__ = 1.0


class QueryDB(object):
    """
    Class defining database query variables.
    """

    FIELDS = ['Name','Lastname', 'Phone', 'Direction', 'Email', 'Web']

    SQL_CHECK = """
        SELECT version()
        """
    SQL_CREATE = """
        CREATE TABLE IF NOT EXISTS Contacts(
            Contact_id SERIAL PRIMARY KEY,
            Name VARCHAR(25) NOT NULL,
            Lastname VARCHAR(25) NOT NULL,
            Phone VARCHAR(25),
            Direction VARCHAR(150),
            Email VARCHAR(50),
            Web VARCHAR(150))
        """
    SQL_INSERT = """
        INSERT INTO Contacts(Name, Lastname, Phone, Direction, Email, Web)
            VALUES(%(name)s, %(lastname)s, %(phone)s, %(direction)s, %(email)s, %(web)s)
            RETURNING Contact_id
        """
    SQL_UPDATE = """
        UPDATE Contacts
            SET Name = %(name)s,
                Lastname = %(lastname)s,
                Phone = %(phone)s,
                Direction = %(direction)s,
                Email = %(email)s,
                Web = %(web)s
            WHERE Contact_id = %(contact_id)s
        """
    SQL_SELECT = """
        SELECT * FROM Contactos WHERE
        """
    SQL_SORT = """
        ORDER BY Name ASC, Lastname ASC
        """
    SQL_SELECT_ALL = """
        SELECT Contact_id, Name, Lastname FROM Contacts
        """
    SQL_DELETE = """
        DELETE FROM Contacts WHERE Contact_id = %(contact_id)s
        """

    def __str__(self):
        """
        Returns a dictionary string representation with the queries.
        """
        queries = {'classname': self.__class__.__name__}
        for query in self.__class__.queries_dict():
            queries.update({'{}'.format(query[0]): query[1]})
        return str(queries)

    @classmethod
    def queries_dict(cls):
        """
        Returns a dictionary with defined queries.
        """
        queries_dict = self.__class__.__dict__
        del queries_dict[FIELDS]
        return queries_dict
