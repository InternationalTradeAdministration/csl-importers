from . import country_code, convert_date

import logging


def get_ids(entries):
    ids = []
    for id in entries:
        id = {
            child.tag.lower().replace("{http://tempuri.org/sdnlist.xsd}id", ""): child.text.strip()
            for child in id
            if child.text and len(child.text.strip()) > 0 and "uid" not in child.tag
        }
        id_keys = [*id]
        if 'country' in id_keys:
            id['country'] = country_code.get_country_code(id['country'])
        id['issue_date'] = None
        id['expiration_date'] = None
        ids.append(id)
    return ids


def get_nationalities(entries):
    nats = []
    for nat in entries:
        nat = {
            child.tag.lower().replace("{http://tempuri.org/sdnlist.xsd}", ""): child.text.strip()
            for child in nat
            if child.text and len(child.text.strip()) > 0 and "country" in child.tag
        }
        nats.append(country_code.get_country_code(nat['country']))
    return nats


def get_places_of_birth(entries):
    places_of_birth = []
    for pob in entries:
        pob = {
            child.tag.lower().replace("{http://tempuri.org/sdnlist.xsd}", ""): child.text.strip()
            for child in pob
            if child.text and len(child.text.strip()) > 0
        }
        pob_keys = [*pob]
        if 'placeofbirth' in pob_keys:
            places_of_birth.append(pob['placeofbirth'])
    return places_of_birth


def get_dates_of_birth(entries):
    dates_of_birth = []
    for dob in entries:
        dob = {
            child.tag.lower().replace("{http://tempuri.org/sdnlist.xsd}", ""): child.text.strip()
            for child in dob
            if child.text and len(child.text.strip()) > 0
        }
        dob_keys = [*dob]
        if 'dateofbirth' in dob_keys:
            parsed_date = convert_date.parse_date(dob['dateofbirth'])
            dates_of_birth.append(parsed_date)
    return dates_of_birth


def get_addresses(entries):
    try:
        addresses = {
            child.tag.lower().replace("{http://tempuri.org/sdnlist.xsd}", ""): child.text.strip()
            for address in entries
            for child in address
            if child.text and len(child.text.strip()) > 0 and "uid" not in child.tag
        }
        address_keys = [*addresses]
        if 'country' in address_keys:
            addresses['country'] = country_code.get_country_code(addresses['country'])
        if 'address1' in address_keys:
            addresses['address'] = addresses['address1']
            del addresses['address1']
        if 'postalcode' in address_keys:
            addresses['postal_code'] = addresses['postalcode']
            del addresses['postalcode']
        return [addresses]
    except LookupError:
        return None


def make_flat_address(address):
    address_list = []
    try:
        for addr in address:
            temp = []
            for address_part in 'address', 'city', 'state', 'postal_code', 'country':
                p = addr.get(address_part)
                p and temp.append(p)
            address_list.append(', '.join(temp))
        return '; '.join(address_list)
    except TypeError:
        return None


def get_multiline_addresses(entries):
    addresses = []
    for address in entries:
        try:
            address = {
                child.tag.lower().replace("{http://tempuri.org/sdnlist.xsd}", ""): child.text.strip()
                for child in address
                if child.text and len(child.text.strip()) > 0 and "uid" not in child.tag
            }
            if not address:
                continue
            address_keys = [*address]
            if 'address1' in address_keys:
                address['address'] = address['address1']
                del address['address1']
            else:
                address['address'] = None
            if 'address2' in address_keys:
                address['address'] = f"{address['address']}, {address['address2']}"
                del address['address2']
            if 'address3' in address_keys:
                address['address'] = f"{address['address']}, {address['address3']}"
                del address['address3']
            if 'city' in address_keys:
                address['city'] = address['city']
            else:
                address['city'] = None
            if 'stateorprovince' in address_keys:
                address['state'] = address['stateorprovince']
                del address['stateorprovince']
            else:
                address['state'] = None
            if 'postalcode' in address_keys:
                address['postal_code'] = address['postalcode']
                del address['postalcode']
            else:
                address['postal_code'] = None
            if 'country' in address_keys:
                address['country'] = country_code.get_country_code(address['country'])
            else:
                address['country'] = None
            addresses.append(address)
        except KeyError as e:
            logging.info(f"Passed on key error: {e}")
    return addresses
