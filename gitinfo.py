"""Helper functions for retrieving data via the GitHub API.

auth() -----------> Return credentials for use in GitHub API calls.
auth_user() ------> Set GitHub user for subsequent API calls.

memberfields() ---> Get field values for a member/user.
members() --------> Get members of one or more organizations.
membersget() -----> Get member info for a specified organization.

pagination() -----> Parse values from 'link' HTTP header returned by GitHub API.

repofields() -----> Get field values for a repo.
repos() ----------> Get repo information for organization(s) or user(s).
reposget() -------> Get repo information from specified API endpoint.

verbose() --------> Set verbose mode on/off.
verbose_output() -> Display status info in verbose mode.

write_csv() ------> Write a list of namedtuples to a CSV file.
"""
import collections
import csv
import json
import traceback

import requests

#------------------------------------------------------------------------------
class _settings: # pylint: disable=R0903
    """Used for global settings. Should not be accessed directly - e.g.,
    use the verbose() function to change _settings.verbose, or the user()
    function to change _settings.github_username/accesstoken.
    """
    verbose = False # default = verbose mode off
    github_username = None # default = no GitHub authentication
    github_accesstoken = None

#------------------------------------------------------------------------------
def auth():
    """Credentials for basic authentication.

    Returns the tuple used for API calls, based on current settings.
    Returns None if no GitHub username/PAT is current set.
    """
    # Note that "auth() ->" is explcitly added to the verbose_output()
    # calls below because auth() is typically used inline from other
    # functions, so it isn't the caller in the call stack.

    if not _settings.github_username:
        return None

    username = _settings.github_username
    access_token = _settings.github_accesstoken

    verbose_output('auth() ->', 'username:', username + ', PAT:',
                   access_token[0:2] + '...' + access_token[-2:])

    return (username, access_token)

#-------------------------------------------------------------------------------
def auth_user(username=None):
    """Set GitHub user for subsequent API calls.

    username = a GitHub username stored in github_users.json in the
               /private subfolder. If omitted or None, resets GitHub user to
               no authentication.
    """
    if username:
        with open('private/github_users.json', 'r') as jsonfile:
            github_users = json.load(jsonfile)
            _settings.github_username = username
            _settings.github_accesstoken = github_users[username]
    else:
        # no username specified, so reset to default of no authentication
        _settings.github_username = None
        _settings.github_accesstoken = None

#-------------------------------------------------------------------------------
def memberfields(member_json, fields, org):
    """Get field values for a member/user.

    1st parameter = member's json representation as returned by GitHub API
    2nd parameter = list of names of desired fields
    3rd parameter = organization ID

    Returns a namedtuple containing the desired fields and their values.
    NOTE: in addition to the specified fields, always returns an 'org' field
    to distinguish between organizations in lists returned by members().
    """
    values = {}
    values['org'] = org
    for fldname in fields:
        values[fldname] = member_json[fldname]

    member_tuple = collections.namedtuple('member_tuple',
                                          'org ' + ' '.join(fields))
    return member_tuple(**values)

#-------------------------------------------------------------------------------
def members(org=None, fields=None, audit2fa=False):
    """Get members for one or more organizations.

    org = organization
    fields = list of field names to be returned; names must be the same as
             returned by the GitHub API (see below).
    audit2fa = whether to only return members with 2FA disabled. You must be
               authenticated via auth_user() as an admin of the org(s) to use
               this option.

    Returns a list of namedtuple objects, one per member.

    GitHub API fields (as of March 2016):
    id                  events_url          organizations_url
    login               followers_url       received_events_url
    site_admin          following_url       repos_url
    type                gists_url           starred_url
    url                 gravatar_id         subscriptions_url
    avatar_url          html_url
    """
    if not fields:
        fields = ['login', 'id', 'type', 'site_admin'] # default field list

    memberlist = [] # the list of members that will be returned

    # org may be a single value as a string, or a list of values
    if isinstance(org, str):
        memberlist.extend(membersget(org, fields, audit2fa))
    else:
        for orgid in org:
            memberlist.extend(membersget(orgid, fields, audit2fa))

    return memberlist

#------------------------------------------------------------------------------
def membersget(org, fields, audit2fa=False):
    """Get member info for a specified organization.

    1st parameter = organization ID
    2nd parameter = list of fields to be returned
    audit2fa = whether to only return members with 2FA disabled.
               Note: for audit2fa=True, you must be authenticated via
               auth_user() as an admin of the org(s).

    Returns a list of namedtuples containing the specified fields.
    """
    endpoint = 'https://api.github.com/orgs/' + org + '/members' + \
        ('?filter=2fa_disabled' if audit2fa else '')
    retval = [] # the list to be returned
    totpages = 0

    while True:

        # GitHub API call
        response = requests.get(endpoint, auth=auth())
        verbose_output('API rate limit: {0}, remaining: {1}'. \
            format(response.headers['X-RateLimit-Limit'],
                   response.headers['X-RateLimit-Remaining']))

        if response.ok:
            totpages += 1
            thispage = json.loads(response.text)
            for member_json in thispage:
                retval.append(memberfields(member_json, fields, org))

        pagelinks = pagination(response)
        endpoint = pagelinks['nextURL']
        if not endpoint:
            break # no more results to process

        verbose_output('processing page {0} of {1}'. \
                       format(pagelinks['nextpage'], pagelinks['lastpage']))

    verbose_output('pages processed: {0}, total members: {1}'. \
        format(totpages, len(retval)))

    return retval

#------------------------------------------------------------------------------
def pagination(link_header):
    """Parse values from the 'link' HTTP header returned by GitHub API.

    1st parameter = either of these options ...
                    - 'link' HTTP header passed as a string
                    - response object returned by requests.get()

    Returns a dictionary with entries for the URLs and page numbers parsed
    from the link string: firstURL, firstpage, prevURL, prevpage, nextURL,
    nextpage, lastURL, lastpage.
    """
    # initialize the dictionary
    retval = {'firstpage':0, 'firstURL':None, 'prevpage':0, 'prevURL':None,
              'nextpage':0, 'nextURL':None, 'lastpage':0, 'lastURL':None}

    if isinstance(link_header, str):
        link_string = link_header
    else:
        # link_header is a response object, get its 'link' HTTP header
        try:
            link_string = link_header.headers['Link']
        except KeyError:
            return retval # no Link HTTP header found, nothing to parse

    links = link_string.split(',')
    for link in links:
        # link format = '<url>; rel="type"'
        linktype = link.split(';')[-1].split('=')[-1].strip()[1:-1]
        url = link.split(';')[0].strip()[1:-1]
        pageno = url.split('?')[-1].split('=')[-1].strip()

        retval[linktype + 'page'] = pageno
        retval[linktype + 'URL'] = url

    return retval

#-------------------------------------------------------------------------------
def repofields(repo_json, fields):
    """Get field values for a repo.

    1st parameter = repo's json representation as returned by GitHub API
    2nd parameter = list of names of desired fields

    Returns a namedtuple containing the desired fields and their values.
    """

    # change '.' to '_' because can't have '.' in an identifier
    fldnames = [_.replace('.', '_') for _ in fields]

    repo_tuple = collections.namedtuple('Repo', ' '.join(fldnames))

    values = {}
    for fldname in fields:
        if '.' in fldname:
            # special case - embedded field within a JSON object
            try:
                values[fldname.replace('.', '_')] = \
                    repo_json[fldname.split('.')[0]][fldname.split('.')[1]]
            except TypeError:
                values[fldname.replace('.', '_')] = None
        else:
            # simple case: copy a value from the JSON to the namedtuple
            values[fldname] = repo_json[fldname]

    return repo_tuple(**values)

#-------------------------------------------------------------------------------
def repos(org=None, user=None, fields=None):
    """Get repo information for organization(s) or user(s).

    org    = organization; an organization or list of organizations
    user   = username; a username or list of usernames
    fields = list of fields to be returned; names must be the same as
             returned by the GitHub API (see below).
             Note: dot notation for embedded elements is supported.
             For example, pass a field named 'license.name' to get the 'name'
             element of the 'license' entry for each repo.

    Returns a list of namedtuple objects, one per repo.

    GitHub API fields (as of March 2016):
    archive_url         git_tags_url         open_issues
    assignees_url       git_url              open_issues_count
    blobs_url           has_downloads        private
    branches_url        has_issues           pulls_url
    clone_url           has_pages            pushed_at
    collaborators_url   has_wiki             releases_url
    commits_url         homepage             size
    compare_url         hooks_url            ssh_url
    contents_url        html_url             stargazers_count
    contributors_url    id                   stargazers_url
    created_at          issue_comment_url    statuses_url
    default_branch      issue_events_url     subscribers_url
    deployments_url     issues_url           subscription_url
    description         keys_url             svn_url
    downloads_url       labels_url           tags_url
    events_url          language             teams_url
    fork                languages_url        trees_url
    forks               master_branch        updated_at
    forks_count         merges_url           url
    forks_url           milestones_url       watchers
    full_name           mirror_url           watchers_count
    git_commits_url     name
    git_refs_url        notifications_url
    -------------------------------------------------------------
    license.featured              permissions.admin
    license.key                   permissions.pull
    license.name                  permissions.push
    license.url
    -------------------------------------------------------------
    owner.avatar_url              owner.organizations_url
    owner.events_url              owner.received_events_url
    owner.followers_url           owner.repos_url
    owner.following_url           owner.site_admin
    owner.gists_url               owner.starred_url
    owner.gravatar_id             owner.subscriptions_url
    owner.html_url                owner.type
    owner.id                      owner.url
    owner.login
    """
    if not fields:
        fields = ['full_name', 'watchers', 'forks', 'open_issues'] # default

    repolist = [] # the list that will be returned

    if org:
        # get repos by organization
        if isinstance(org, str):
            # one organization
            endpoint = 'https://api.github.com/orgs/' + org + '/repos'
            repolist.extend(reposget(endpoint, fields))
        else:
            # list of organizations
            for orgid in org:
                endpoint = 'https://api.github.com/orgs/' + orgid + '/repos'
                repolist.extend(reposget(endpoint, fields))
    else:
        # get repos by user
        if isinstance(user, str):
            # one user
            endpoint = 'https://api.github.com/users/' + user + '/repos'
            repolist.extend(reposget(endpoint, fields))
        else:
            # list of users
            for userid in user:
                endpoint = 'https://api.github.com/users/' + userid + '/repos'
                repolist.extend(reposget(endpoint, fields))

    return repolist

#-------------------------------------------------------------------------------
def reposget(endpoint, fields):
    """Get repo information from specified API endpoint.

    1st parameter = GitHub API endpoint
    2nd parameter = list of fields to be returned

    Returns a list of namedtuples containing the specified fields.
    """
    totpages = 0
    retval = [] # the list to be returned

    # custom header to retrieve license info while License API is in preview
    headers = {'Accept': 'application/vnd.github.drax-preview+json'}

    while True:

        # GitHub API call
        response = requests.get(endpoint, auth=auth(), headers=headers)
        verbose_output('API rate limit: {0}, remaining: {1}'. \
            format(response.headers['X-RateLimit-Limit'],
                   response.headers['X-RateLimit-Remaining']))

        if response.ok:
            totpages += 1
            thispage = json.loads(response.text)
            for repo_json in thispage:
                retval.append(repofields(repo_json, fields))

        pagelinks = pagination(response)
        endpoint = pagelinks['nextURL']
        if not endpoint:
            break # there are no more results to process

        verbose_output('processing page {0} of {1}'. \
                       format(pagelinks['nextpage'], pagelinks['lastpage']))

    verbose_output('pages processed: {0}, total members: {1}'. \
        format(totpages, len(retval)))

    return retval

#-------------------------------------------------------------------------------
def verbose(*args):
    """Set verbose mode on/off.

    1st parameter = True for verbose mode, False to turn verbose mode off.

    Returns the current verbose mode setting as True/False. To query the
    current setting, call verbose() with no parameters.
    """
    if len(args) == 1:
        _settings.verbose = args[0]

    return _settings.verbose

#-------------------------------------------------------------------------------
def verbose_output(*args):
    """Display status information in verbose mode.

    parameters = message to be displayed if verbose(True) is set.

    NOTE: can pass any number of parameters, which will be displayed as a single
    string delimited by spaces.
    """
    if not _settings.verbose:
        return # verbose mode is off

    # convert all arguments to strings. so they can be .join()ed
    string_args = [str(_) for _ in args]

    # get the caller of verbose_output(), which is displayed with the message
    caller = traceback.format_stack()[1].split(',')[2].strip().split()[1]

    print(caller + '() ->', ' '.join(string_args))

#-------------------------------------------------------------------------------
def write_csv(listobj, filename):
    """Write a list of namedtuples to a CSV file.

    1st parameter = the list
    2nd parameter = name of CSV file to be written
    """
    csvfile = open(filename, 'w', newline='')

    csvwriter = csv.writer(csvfile, dialect='excel')
    header_row = listobj[0]._fields
    csvwriter.writerow(header_row)

    for row in listobj:
        values = []
        for fldname in header_row:
            values.append(getattr(row, fldname))
        csvwriter.writerow(values)

    csvfile.close()

    verbose_output('filename:', filename)
    verbose_output('columns:', header_row)
    verbose_output('total rows:', len(listobj))

#===============================================================================
#------------------------------------ TESTS ------------------------------------
#===============================================================================

#-------------------------------------------------------------------------------
def test_auth():
    """Simple test for auth() function.
    """
    print(auth())

#-------------------------------------------------------------------------------
def test_members():
    """Simple test for members() function.
    """
    print(members(org=['bitstadium', 'liveservices']))
    print('total members returned:', len(members(org=['bitstadium', 'liveservices'])))

#-------------------------------------------------------------------------------
def test_repos():
    """Simple test for repos() function.
    """
    oct_repos = repos(user=['octocat'],
                      fields=['full_name', 'license.name', 'license', 'permissions.admin'])
    for repo in oct_repos:
        print(repo)

#-------------------------------------------------------------------------------
def test_pagination():
    """Simple test for pagination() function.
    """
    testlinks = "<https://api.github.com/organizations/6154722/" + \
        "repos?page=2>; rel=\"next\", <https://api.github.com/" + \
        "organizations/6154722/repos?page=18>; rel=\"last\""
    print(pagination(testlinks))

# if running standalone, run tests ---------------------------------------------
if __name__ == "__main__":

    verbose(True) # turn on verbose mode
    auth_user('dmahugh')
    #test_auth()
    #test_members()
    test_repos()
    #test_pagination()
