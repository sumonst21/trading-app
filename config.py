from configparser import ConfigParser


def configemail():

    EMAIL_SETTINGS = {
        'email_address': ''
        'email_password': '',
        'email_host': 'smtp.gmail.com',
        'email_port': 465,
        'email_to': ''
    }

    return EMAIL_SETTINGS

# database 

def configdb(filename='database.ini', section='postgresql'):
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename)
 
    # get section, default to postgresql
    db = {}
    
    # Checks to see if section (postgresql) parser exists
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
         
    # Returns an error if a parameter is called that is not listed in the initialization file
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))
 
    return db



