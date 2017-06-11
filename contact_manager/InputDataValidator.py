#!/usr/bin/python

import re


__all__ = ['InputDataValidator', 'InputDataError']
__version__ = 1.0


class InputDataError(ValueError):
    """
    Exception for invalid input data.
    """

    def __init__(self, msg, original_exception=None):
        if original_exception is not None:
            msg += ": {}".format(original_exception)
        super(InputDataError, self).__init__(msg)
        self.original_exception = original_exception


class InputDataValidator(object):
    """
    Class to validate fetched inputs insterted by user.
    Defines regexes to validate input data against them.
    """

    # Define variables for each regex input type.
    NAME_REGEX = r'([a-zA-Z\.\s]+)'
    LASTNAME_REGEX = r'([a-zA-Z\.-\s]+)'
    PHONE_REGEX = r'((\d{3}|\(\d{3}\))?(\s|-|\.)?\d{3}(\s|-|\.)\d{4}(\s*(ext|x|ext.)\s*\d{2,5})?)'
    EMAIL_REGEX = r'(([a-zA-Z0-9\._%+-]+)@([a-zA-Z0-9\._%+-]+)(\.[a-zA-Z]{2,4}))'
    WEB_REGEX = r'((^(http|https)://)?(www\.)?([a-zA-Z0-9_%-]+)(\.[a-zA-Z]{2,5})))'

    def __init__(self, input_data={}):
        """
        Initializes the validator with input data.
        """
        self._name = input_data.get('Name', None)
        self._lastname = input_data.get('Lastname', None)
        self._phone = input_data.get('Phone', None)
        self._email = input_data.get('Email', None)
        self._web = input_data.get('Web', None)

    def __str__(self):
        """
        Return a string representation including the input data.
        """
        input_data = {
            'classname': self.__class__.__name__,
            'name': self._name,
            'lastname': self._lastname,
            'phone': self._phone,
            'email': self._email,
            'web': self._web,
        }
        return '<{classname}: name={name}, lastname={lastname}, \
                phone={phone}, email={email}, web={web}>'.format(**input_data)

    @classmethod
    def regex_dict(cls):
        """
        Returns the regexes dictionary.
        """
        regex_dict = self.__class__.__dict__
        return regex_dict

    @property
    def name(self):
        """
        Returns the validated "name" input data.
        """
        if self._valid_data(self.__class__.NAME_REGEX, self._name):
            return self._name
        return False

    @property
    def lastname(self):
        """
        Returns the validated "lastname" input data.
        """
        if self._valid_data(self.__class__.LASTNAME_REGEX, self._lastname):
            return self._lastname
        return False

    @property
    def phone(self):
        """
        Returns the validated "phone" input data.
        """
        if self._valid_data(self.__class__.PHONE_REGEX, self._phone):
            return self._phone
        return False

    @property
    def email(self):
        """
        Returns the validated "email" input data.
        """
        if self._valid_data(self.__class__.EMAIL_REGEX, self._email):
            return self._email
        return False

    @property
    def web(self):
        """
        Return the validated "web" input data.
        """
        if self._valid_data(self.__class__.WEB_REGEX, self._web):
            return self._web
        return False

    def _valid_data(self, regex, data):
        """
        Validates individual input data against
        its corresponding regex.
        """
        try:
            matched_object = self._match_data(pattern, data)
            if matched_object is not None:
                return True
        except InputDataError as msg:
            print('Error validating {} input data:\n'.format(data_name.lstrip('_')), msg, sep='')
        return False

    def _validate_input_data(self):
        """
        Validates all the input data against
        corresponding regex.
        """
        for pattern_name, pattern in self.__class__.regex_dict().items():
            data_name = ''.join('_', pattern_name.split('_')[0].lower())
            data = self.__dict__[data_name]
            try:
                matched_object = self._match_data(pattern, data)
            except InputDataError as msg:
                print('Error validating {} input data:\n'.format(data_name.lstrip('_')), msg, sep='')
                setattr(self, data_name, None)

    def _match_data(self, pattern, data):
        """
        Matches the input data against regex.
        Returns the main group matched.
        """
        regex = re.compile(pattern)
        match_group = regex.search(data)
        matched = match_group.group(0)
        if matched:
            return matched
        else:
            raise InputDataError('Invalid input: {}'.format(data))
