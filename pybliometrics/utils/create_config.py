import configparser
from typing import List, Optional


def create_config(keys: Optional[List[str]] = None,
                  insttoken: Optional[str] = None
                  ):
    """Initiates process to generate configuration file.

    :param keys: If you provide a list of keys, pybliometrics will skip the
                 prompt.  It will also not ask for InstToken.  This is
                 intended for workflows using CI, not for general use.
    :param insttoken: An InstToken to be used alongside the key(s).  Will only
                      be used if `keys` is not empty.
    """
    from pybliometrics.utils.constants import CONFIG_FILE, DEFAULT_PATHS

    config = configparser.ConfigParser()
    config.optionxform = str
    print(f"Creating config file at {CONFIG_FILE} with default paths...")

    # Set directories
    config.add_section('Directories')
    for api, path in DEFAULT_PATHS.items():
        config.set('Directories', api, str(path))

    # Set authentication for Scopus and SciVal
    section_name='Authentication'
    config.add_section(section_name)
    if keys:
        if not isinstance(keys, list):
            raise ValueError("Parameter `keys` must be a list.")
        key = ", ".join(keys)
        token = insttoken
    else:
        prompt_key = f"Please enter your API Key(s) for Scopus and SciVal, obtained from "\
                     "http://dev.elsevier.com/myapikey.html.  Separate "\
                     "multiple keys by comma:\n"
        key = input(prompt_key)

        prompt_token = "API Keys are sufficient for most users.  If you "\
                    f"have an InstToken for Scopus and SciVal, please enter the token now; "\
                    "otherwise just press Enter:\n"
        token = input(prompt_token)
    config.set(section_name, 'APIKey', key)

    if token:
        config.set(section_name, 'InstToken', token)

    # Set default values
    config.add_section('Requests')
    config.set('Requests', 'Timeout', '20')
    config.set('Requests', 'Retries', '5')

    # Write out
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as ouf:
        config.write(ouf)
    print(f"Configuration file successfully created at {CONFIG_FILE}\n"
          "For details see https://pybliometrics.rtfd.io/en/stable/configuration.html.")
    return config
