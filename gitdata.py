"""GitHub query CLI.

cli() ----------------> Handle command-line arguments.
members() ------------> Get member info for an org or repo.
members_listfields() -> List valid field names for members().
repos() --------------> Get repo info for an org or user.
repos_listfields() ---> List valid field names for repos().
"""
import os

import click
from click.testing import CliRunner

import gitinfo as gi
#------------------------------------------------------------------------------
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.group(context_settings=CONTEXT_SETTINGS, options_metavar='')
@click.version_option(version='1.0', prog_name='Photerino')
def cli():
    """\b
    _______________
      |____________  GitData - retrieves data via GitHub REST API
      |____________
          |________  syntax help: gitdata COMMAND -h/--help
          |________
    """
    pass # this is just for grouping, all functionality is in subcommands

#------------------------------------------------------------------------------
@cli.command()
@click.option('-o', '--org', default='',
              help='GitHub organization', metavar='')
@click.option('-r', '--repo', default='',
              help='GitHub repo', metavar='')
@click.option('-a', '--authuser', default='',
              help='authentication username', metavar='')
@click.option('-n', '--filename', default='',
              help='output filename', metavar='')
@click.option('-j', '--json', is_flag=True,
              help='JSON format (default=CSV)')
@click.option('-f', '--fields', default='',
              help='fields to include', metavar='<fld1/fld2/etc>')
@click.option('-l', '--fieldlist', is_flag=True,
              help='list available GitHub fields')
def members(org, repo, authuser, filename, json, fields, fieldlist):
    """Get member info for an org or repo.
    """
    if fieldlist:
        members_listfields()
        return

    if not org:
        click.echo('ERROR: must specify an org')
        return

    if authuser:
        gi.auth_config({'username': authuser})

    click.echo('/// members subcommand')

#------------------------------------------------------------------------------
def members_listfields():
    """List valid field names for members().
    """
    click.echo('\nValid GitHub API field names for MEMBERS:\n' + 60*'-')
    click.echo('id                  events_url          organizations_url')
    click.echo('login               followers_url       received_events_url')
    click.echo('site_admin          following_url       repos_url')
    click.echo('type                gists_url           starred_url')
    click.echo('url                 gravatar_id         subscriptions_url')
    click.echo('avatar_url          html_url')

#------------------------------------------------------------------------------
@cli.command()
@click.option('-o', '--org', default='',
              help='GitHub organization', metavar='')
@click.option('-u', '--user', default='',
              help='GitHub user', metavar='')
@click.option('-a', '--authuser', default='',
              help='authentication username', metavar='')
@click.option('-n', '--filename', default='',
              help='output filename', metavar='')
@click.option('-j', '--json', is_flag=True,
              help='JSON format (default=CSV)')
@click.option('-f', '--fields', default='',
              help='fields to include', metavar='<fld1/fld2/etc>')
@click.option('-l', '--fieldlist', is_flag=True,
              help='list available GitHub fields')
def repos(org, user, authuser, filename, json, fields, fieldlist):
    """Get repo info for an org or user.
    """
    if fieldlist:
        repos_listfields()
        return

    if not org and not user:
        click.echo('ERROR: must specify an org or user')
        return

    if authuser:
        gi.auth_config({'username': authuser})

    if fields:
        repolist = gi.repos(org=org, user=user, fields=fields.split('/'))
    else:
        repolist = gi.repos(org=org, user=user)

    for repo in repolist:
        #/// need to design this carefully; allow for CSV or JSON, need a switch for whether to display CSV version to console
        #/// note that order of fields in namedtuple is not determinant, so need to iterate through the passed fieldnames list to get order correct
        for item in repo:
            click.echo(str(item) + ',', nl=False)
        click.echo('')

#------------------------------------------------------------------------------
def repos_listfields():
    """List valid field names for repos().
    """
    click.echo('\nValid GitHub API field names for REPOS:\n' + 60*'-')
    click.echo('archive_url         git_tags_url         open_issues')
    click.echo('assignees_url       git_url              open_issues_count')
    click.echo('blobs_url           has_downloads        private')
    click.echo('branches_url        has_issues           pulls_url')
    click.echo('clone_url           has_pages            pushed_at')
    click.echo('collaborators_url   has_wiki             releases_url')
    click.echo('commits_url         homepage             size')
    click.echo('compare_url         hooks_url            ssh_url')
    click.echo('contents_url        html_url             stargazers_count')
    click.echo('contributors_url    id                   stargazers_url')
    click.echo('created_at          issue_comment_url    statuses_url')
    click.echo('default_branch      issue_events_url     subscribers_url')
    click.echo('deployments_url     issues_url           subscription_url')
    click.echo('description         keys_url             svn_url')
    click.echo('downloads_url       labels_url           tags_url')
    click.echo('events_url          language             teams_url')
    click.echo('fork                languages_url        trees_url')
    click.echo('forks               master_branch        updated_at')
    click.echo('forks_count         merges_url           url')
    click.echo('forks_url           milestones_url       watchers')
    click.echo('full_name           mirror_url           watchers_count')
    click.echo('git_commits_url     name')
    click.echo('git_refs_url        notifications_url')
    click.echo(60*'-')
    click.echo('license.featured              permissions.admin')
    click.echo('license.key                   permissions.pull')
    click.echo('license.name                  permissions.push')
    click.echo('license.url')
    click.echo(60*'-')
    click.echo('owner.avatar_url              owner.organizations_url')
    click.echo('owner.events_url              owner.received_events_url')
    click.echo('owner.followers_url           owner.repos_url')
    click.echo('owner.following_url           owner.site_admin')
    click.echo('owner.gists_url               owner.starred_url')
    click.echo('owner.gravatar_id             owner.subscriptions_url')
    click.echo('owner.html_url                owner.type')
    click.echo('owner.id                      owner.url')
    click.echo('owner.login')

# code to execute when running standalone: -------------------------------------
if __name__ == '__main__':
    print('/// need to implement tests here')