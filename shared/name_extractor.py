ns = {'xmlns': 'http://tempuri.org/sdnList.xsd'}


def get_name(entry, source=None):
    firstname = entry.find('xmlns:firstName', ns)
    lastname = entry.find('xmlns:lastName', ns)

    if firstname is not None:
        if source is not None:
            name = f"{lastname.text.strip()}, {firstname.text.strip()}"
        else:
            name = f"{firstname.text.strip()} {lastname.text.strip()}"
    else:
        name = f"{lastname.text.strip()}"
    return name


def get_alt_names(entries, source=None):
    if source is not None:
        alt_names = [
            get_name(child, 'lastfirst')
            for child in entries
            for name in child
            if name.text and len(name.text.strip()) > 0 and 'lastName' in name.tag
        ]
    else:
        alt_names = [
            get_name(child)
            for child in entries
            for name in child
            if name.text and len(name.text.strip()) > 0 and 'lastName' in name.tag
        ]
    return alt_names if alt_names else []
