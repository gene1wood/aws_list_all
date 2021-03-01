#!/usr/bin/env python
from __future__ import print_function

import os
import sys
import webbrowser
from resource import getrlimit, setrlimit, RLIMIT_NOFILE
from argparse import ArgumentParser
from sys import exit, stderr

from .introspection import (
    get_listing_operations, get_services, get_verbs, introspect_regions_for_service, recreate_caches
)
from .query import do_list_files, do_query, print_query


def increase_limit_nofiles():
    soft_limit, hard_limit = getrlimit(RLIMIT_NOFILE)
    desired_limit = 6000  # This should be comfortably larger than the product of services and regions
    if hard_limit < desired_limit:
        print("-" * 80, file=stderr)
        print(
            "WARNING!\n"
            "Your system limits the number of open files and network connections to {}.\n"
            "This may lead to failures during querying.\n"
            "Please increase the hard limit of open files to at least {}.\n"
            "The configuration for hard limits is often found in /etc/security/limits.conf".format(
                hard_limit, desired_limit
            ),
            file=stderr
        )
        print("-" * 80, file=stderr)
        print(file=stderr)
    target_soft_limit = min(desired_limit, hard_limit)
    if target_soft_limit > soft_limit:
        print("Increasing the open connection limit \"nofile\" from {} to {}.".format(soft_limit, target_soft_limit))
        setrlimit(RLIMIT_NOFILE, (target_soft_limit, hard_limit))
    print("")


def main():
    """Parse CLI arguments to either list services, operations, queries or existing json files"""
    parser = ArgumentParser(
        prog='aws_list_all',
        description=(
            'List AWS resources on one account across regions and services. '
            'Saves result into json files, which can then be passed to this tool again '
            'to list the contents.'
        )
    )
    subparsers = parser.add_subparsers(
        description='List of subcommands. Use <subcommand> --help for more parameters',
        dest='command',
        metavar='COMMAND'
    )

    # Query is the main subcommand, so we put it first
    query = subparsers.add_parser('query', description='Query AWS for resources', help='Query AWS for resources')
    query.add_argument(
        '-s',
        '--service',
        action='append',
        help='Restrict querying to the given service (can be specified multiple times)'
    )
    query.add_argument(
        '-r',
        '--region',
        action='append',
        help='Restrict querying to the given region (can be specified multiple times)'
    )
    query.add_argument(
        '-o',
        '--operation',
        action='append',
        help='Restrict querying to the given operation (can be specified multiple times)'
    )
    query.add_argument('-p', '--parallel', default=32, type=int, help='Number of request to do in parallel')
    query.add_argument('-d', '--directory', default='.', help='Directory to save result listings to')
    query.add_argument('-v', '--verbose', action='count', help='Print detailed info during run')
    query.add_argument('-c', '--profile', help='Use a specific .aws/credentials profile.')

    # Once you have queried, show is the next most important command. So it comes second
    show = subparsers.add_parser(
        'show', description='Show a summary or details of a saved listing', help='Display saved listings'
    )
    show.add_argument('listingfile', nargs='*', help='listing file(s) to load and print')
    show.add_argument('-v', '--verbose', action='count', help='print given listing files with detailed info')

    # Introspection debugging is not the main function. So we put it all into a subcommand.
    introspect = subparsers.add_parser(
        'introspect',
        description='Print introspection debugging information',
        help='Print introspection debugging information'
    )
    introspecters = introspect.add_subparsers(
        description='Pieces of debug information to collect. Use <DETAIL> --help for more parameters',
        dest='introspect',
        metavar='DETAIL'
    )

    introspecters.add_parser(
        'list-services',
        description='Lists short names of AWS services that the current boto3 version has clients for.',
        help='List available AWS services'
    )
    introspecters.add_parser(
        'list-service-regions',
        description='Lists regions where AWS services are said to be available.',
        help='List AWS service regions'
    )
    ops = introspecters.add_parser(
        'list-operations',
        description='List all discovered listing operations on all (or specified) services',
        help='List discovered listing operations'
    )
    ops.add_argument(
        '-s',
        '--service',
        action='append',
        help='Only list discovered operations of the given service (can be specified multiple times)'
    )
    introspecters.add_parser('debug', description='Debug information', help='Debug information')

    # Print to an HTML file to be viewed in a browser
    viewhtml = subparsers.add_parser(
        'print-html', description='Print a listing to an HTML file to be viewed in a browser',
        help='Create browser view of listing'
    )
    viewhtml.add_argument(
        '-s',
        '--service',
        action='append',
        help='Restrict querying to the given service (can be specified multiple times)'
    )
    viewhtml.add_argument(
        '-r',
        '--region',
        action='append',
        help='Restrict querying to the given region (can be specified multiple times)'
    )
    viewhtml.add_argument(
        '-o',
        '--operation',
        action='append',
        help='Restrict querying to the given operation (can be specified multiple times)'
    )
    viewhtml.add_argument('-p', '--parallel', default=32, type=int, help='Number of request to do in parallel')
    viewhtml.add_argument('-d', '--directory', default='.', help='Directory to save result listings to')
    viewhtml.add_argument('-v', '--verbose', action='count', help='Print detailed info during run')
    viewhtml.add_argument('-c', '--profile', help='Use a specific .aws/credentials profile.')

    # Finally, refreshing the service/region caches comes last.
    caches = subparsers.add_parser(
        'recreate-caches',
        description=(
            'The list of AWS services and endpoints can change over time. '
            'This command (re-)creates the caches for this data to allow you to'
            'list services in regions where they have not been available previously.'
            'The cache lives in your OS-dependent cache directory, e.g. ~/.cache/aws_list_all/'
        ),
        help='Recreate service and region caches'
    )
    caches.add_argument(
        '--update-packaged-values',
        action='store_true',
        help=(
            'Instead of writing to the cache, update files packaged with aws-list-all. '
            'Use this only if you run a copy from git.'
        )
    )

    args = parser.parse_args()

    if args.command == 'query':
        if args.directory:
            try:
                os.makedirs(args.directory)
            except OSError:
                pass
            os.chdir(args.directory)
        increase_limit_nofiles()
        services = args.service or get_services()
        do_query(
            services,
            args.region,
            args.operation,
            verbose=args.verbose or 0,
            parallel=args.parallel,
            selected_profile=args.profile
        )
    elif args.command == 'show':
        if args.listingfile:
            increase_limit_nofiles()
            do_list_files(args.listingfile, verbose=args.verbose or 0)
        else:
            show.print_help()
            return 1
    elif args.command == 'introspect':
        if args.introspect == 'list-services':
            for service in get_services():
                print(service)
        elif args.introspect == 'list-service-regions':
            introspect_regions_for_service()
            return 0
        elif args.introspect == 'list-operations':
            for service in args.service or get_services():
                for operation in get_listing_operations(service):
                    print(service, operation)
        elif args.introspect == 'debug':
            for service in get_services():
                for verb in get_verbs(service):
                    print(service, verb)
        else:
            introspect.print_help()
            return 1
    elif args.command == 'print-html':
        origout = sys.stdout
        f = open("test.html", 'w')
        sys.stdout = f
        print('<!DOCTYPE html>\n<html>\n')
        print('<head>\n<style>\n')
        print('table, th, td {border: 1px solid black; border-collapse: collapse; table-layout:fixed;}\n')
        print('.nfound {border: 10px solid Orange; padding: 10px;}\n')
        print('.found {border: 10px solid LightGreen; padding: 10px;}\n')
        print('.error {border: 10px solid Red; padding: 10px;}\n')
        print('.denied {border: 10px solid Blue; padding: 10px;}\n')
        # for region in region_colors:
        #     print('.' + region + '{border: 5px solid ' + region_colors[region]
        #         + '; padding: 10px; position: relative;}\n'
        #         + '.' + region + ':after {margin: -1rem; content: "'
        #         +  region.upper() + '"; font-size: 40px; position: absolute; '
        #         + 'color: rgb(210, 210, 210); z-index: -1; left: 50%; margin-left: -20%;}\n')
        #print('th, td {padding: 10px;}')
        print('.nCollapse {background-color: Orange; color: white; cursor: pointer; '
            + 'padding: 14px; width: 100%; border: none; text-align: left; font-size: 20px;}\n')
        print('.fCollapse {background-color: LightGreen; color: white; cursor: pointer; '
            + 'padding: 14px; width: 100%; border: none; text-align: left; font-size: 20px;}\n')
        print('.eCollapse {background-color: Red; color: white; cursor: pointer; '
            + 'padding: 14px; width: 100%; border: none; text-align: left; font-size: 20px;}\n')
        print('.dCollapse {background-color: Blue; color: white; cursor: pointer; '
            + 'padding: 14px; width: 100%; border: none; text-align: left; font-size: 20px;}\n')
        print('.active, .nCollapse:hover {background-color: #777;}\n')
        print('.active, .fCollapse:hover {background-color: #777;}\n')
        print('.active, .eCollapse:hover {background-color: #777;}\n')
        print('.active, .dCollapse:hover {background-color: #777;}\n')
        print('.content {display: none; overflow: hidden; background-color: #f1f1f1;}\n')
        print('</style>\n</head>\n<body>\n')
        if args.directory:
            try:
                os.makedirs(args.directory)
            except OSError:
                pass
            os.chdir(args.directory)
        increase_limit_nofiles()
        services = args.service or get_services()
        print_query(
            services,
            args.region,
            args.operation,
            verbose=args.verbose or 0,
            parallel=args.parallel,
            selected_profile=args.profile
        )
        print('<script>\n'
            #+ 'var coll = document.getElementsByClassName("collapsible");\n'
            + 'var coll = document.querySelectorAll(".nCollapse,.fCollapse,.eCollapse,.dCollapse");'
            + 'var i;\n'
            + 'for (i = 0; i < coll.length; i++) {\n'
            + '  coll[i].addEventListener("click", function() {\n'
            + '    this.classList.toggle("active");\n'
            + '    var content = this.nextElementSibling;\n'
            + '    if (content.style.display === "block") {\n'
            + '      content.style.display = "none";\n'
            + '    } else {\n'
            + '      content.style.display = "block";\n'
            + '    }\n'
            + '  });\n'
            + '}\n')
        print('</script>\n')
        print('\n</body>\n</html>')
        sys.stdout = origout

        new = 2
        url = "/home/devuser/BA-thesis/aws_list_all/test.html"
        webbrowser.open(url,new=new)
    elif args.command == 'recreate-caches':
        increase_limit_nofiles()
        recreate_caches(args.update_packaged_values)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    exit(main())
