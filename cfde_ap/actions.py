import logging
import uuid
from deriva.core import DerivaServer

from cfde_ap import CONFIG
from cfde_ap.auth import get_dependent_token, get_webauthn_user
from cfde_deriva.registry import Registry, WebauthnUser
from cfde_deriva.submission import Submission



logger = logging.getLogger(__name__)


def deriva_ingest(servername, archive_url, dcc_id=None, globus_ep=None, action_id=None):
    """Perform an ingest to DERIVA into a catalog, using the CfdeDataPackage.

    Arguments:
        servername (str): The name of the DERIVA server.
        data_json_file (str): The path to the JSON file with TableSchema data.
        catalog_id (str or int): If updating an existing catalog, the existing catalog ID.
                Default None, to create a new catalog.
        acls (dict): The ACLs to set on the catalog.
                Default None to use default ACLs.

    Returns:
        dict: The result of the ingest.
            success (bool): True when the ingest was successful.
            catalog_id (str): The catalog's ID.
    """
    credential = {
        "bearer-token": get_dependent_token(CONFIG["DEPENDENT_SCOPES"]["deriva_all"])
    }
    registry = Registry('https', servername, credentials=credential)
    server = DerivaServer('https', servername, credential)
    submitting_user = get_webauthn_user()

    https_token = get_dependent_token(f'https://auth.globus.org/scopes/{globus_ep}/https')
    # the Globus action_id is used as the Submission id, this allows us to track submissions
    # in Deriva back to an action.
    submission_id = action_id
    logger.info(f'Submitting new dataset into Deriva using submission id {submission_id}')

    # pre-flight check like action provider might want to do?
    # this is optional, implicitly happening again in Submission(...)
    registry.validate_dcc_id(dcc_id, submitting_user)

    # Submission.content_path_root = CONFIG['DATA_DIR']
    # run the actual submission work if we get this far
    submission = Submission(server, registry, submission_id, dcc_id, archive_url, submitting_user,
                            globus_https_token=https_token)
    submission.ingest()

    md = registry.get_datapackage(submission_id)
    return {
        "success": True,
        "catalog_id": submission_id,
        "catalog_url": md['review_browse_url']
    }
