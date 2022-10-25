import pycountry


def get_country_code(country_name):
    if len(country_name) == 0:
        return country_name
    country_name = country_name.lower()
    if country_name == 'brunei':
        return 'BN'
    elif country_name == 'bahamas, the':
        return 'BS'
    elif country_name == 'burma':
        return 'MM'
    elif country_name in ['cabo verde', 'cabo verde.  previously cape verde.']:
        return 'CV'
    elif country_name == 'cote d ivoire':
        return 'CI'
    elif country_name.lower() in ['congo, democratic republic of the', 'congo, republic of the']:
        return 'CG'
    elif country_name.lower() == "china":
        return "CN"
    elif country_name in ['crimea', 'crimea (occupied)', 'region: crimea']:
        return 'crimea (occupied)'
    elif country_name == 'the gambia':
        return 'GM'
    elif country_name in ['honk kong', 'kong kong']:
        return 'HK'
    elif country_name == 'iran':
        return 'IR'
    elif country_name.lower() in ['korea, north', 'north korea']:
        return 'KP'
    elif country_name.lower() in ['korea, south', 'south korea']:
        return 'KR'
    elif country_name.lower() == 'kosovo':
        return 'XK'
    elif country_name == 'macao':
        return 'MO'
    elif country_name == 'moracco':
        return 'MA'
    elif country_name.lower() == 'netherlands antilles':
        return 'AN'
    elif country_name.lower() == 'north macedonia, the republic of':
        return 'MK'
    elif country_name.lower() in ['palestinian', 'region: gaza', 'west bank']:
        return 'PS'
    elif country_name == 'russia':
        return 'RU'
    elif country_name == 'syria':
        return 'SY'
    elif country_name in ['uae', 'u.a.e.', 'united arab emirates (uae)']:
        return 'AE'
    else:
        try:
            return pycountry.countries.lookup(country_name).alpha_2
        except LookupError:
            return country_name
