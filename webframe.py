#!/usr/bin/env python3
#
# Copyright 2019 Miklos Vajna. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#

"""The webframe module provides the header, toolbar and footer code."""

from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import TYPE_CHECKING
from typing import Tuple
from typing import cast
import datetime
import os
import traceback

import pytz
import yattag

from i18n import translate as _
import areas
import config
import util
import version

if TYPE_CHECKING:
    # pylint: disable=no-name-in-module,import-error,unused-import
    from wsgiref.types import StartResponse


def get_footer(last_updated: str = "") -> yattag.doc.Doc:
    """Produces the end of the page."""
    items: List[yattag.doc.Doc] = []
    doc = yattag.doc.Doc()
    doc.text(_("Version: "))
    doc.asis(util.git_link(version.VERSION, "https://github.com/vmiklos/osm-gimmisn/commit/").getvalue())
    items.append(doc)
    items.append(util.html_escape(_("OSM data © OpenStreetMap contributors.")))
    if last_updated:
        items.append(util.html_escape(_("Last update: ") + last_updated))
    doc = yattag.doc.Doc()
    doc.stag("hr")
    with doc.tag("div"):
        for index, item in enumerate(items):
            if index:
                doc.text(" ¦ ")
            doc.asis(item.getvalue())
    return doc


def fill_header_function(function: str, relation_name: str, items: List[yattag.doc.Doc]) -> None:
    """Fills items with function-specific links in the header. Returns a title."""
    prefix = config.Config.get_uri_prefix()
    if function == "missing-housenumbers":
        # The OSM data source changes much more frequently than the ref one, so add a dedicated link
        # to update OSM house numbers first.
        doc = yattag.doc.Doc()
        with doc.tag("a", href=prefix + "/street-housenumbers/" + relation_name + "/update-result"):
            doc.text(_("Update from OSM"))
        items.append(doc)

        doc = yattag.doc.Doc()
        with doc.tag("a", href=prefix + "/missing-housenumbers/" + relation_name + "/update-result"):
            doc.text(_("Update from reference"))
        items.append(doc)
    elif function == "missing-streets":
        # The OSM data source changes much more frequently than the ref one, so add a dedicated link
        # to update OSM streets first.
        doc = yattag.doc.Doc()
        with doc.tag("a", href=prefix + "/streets/" + relation_name + "/update-result"):
            doc.text(_("Update from OSM"))
        items.append(doc)

        doc = yattag.doc.Doc()
        with doc.tag("a", href=prefix + "/missing-streets/" + relation_name + "/update-result"):
            doc.text(_("Update from reference"))
        items.append(doc)
    elif function == "street-housenumbers":
        doc = yattag.doc.Doc()
        with doc.tag("a", href=prefix + "/street-housenumbers/" + relation_name + "/update-result"):
            doc.text(_("Call Overpass to update"))
        items.append(doc)
        doc = yattag.doc.Doc()
        with doc.tag("a", href=prefix + "/street-housenumbers/" + relation_name + "/view-query"):
            doc.text(_("View query"))
        items.append(doc)
    elif function == "streets":
        doc = yattag.doc.Doc()
        with doc.tag("a", href=prefix + "/streets/" + relation_name + "/update-result"):
            doc.text(_("Call Overpass to update"))
        items.append(doc)
        doc = yattag.doc.Doc()
        with doc.tag("a", href=prefix + "/streets/" + relation_name + "/view-query"):
            doc.text(_("View query"))
        items.append(doc)


def fill_missing_header_items(streets: str, relation_name: str, items: List[yattag.doc.Doc]) -> None:
    """Generates the 'missing house numbers/streets' part of the header."""
    prefix = config.Config.get_uri_prefix()
    if streets != "only":
        doc = yattag.doc.Doc()
        with doc.tag("a", href=prefix + "/missing-housenumbers/" + relation_name + "/view-result"):
            doc.text(_("Missing house numbers"))
        doc.text(" (")
        with doc.tag("a", href=prefix + "/missing-housenumbers/" + relation_name + "/view-result.txt"):
            doc.text("txt")
        doc.text(", ")
        with doc.tag("a", href=prefix + "/missing-housenumbers/" + relation_name + "/view-result.chkl"):
            doc.text("chkl")
        doc.text(")")
        items.append(doc)
    if streets != "no":
        doc = yattag.doc.Doc()
        with doc.tag("a", href=prefix + "/missing-streets/" + relation_name + "/view-result"):
            doc.text(_("Missing streets"))
        doc.text(" (")
        with doc.tag("a", href=prefix + "/missing-streets/" + relation_name + "/view-result.txt"):
            doc.text("txt")
        doc.text(")")
        items.append(doc)


def fill_existing_header_items(streets: str, relation_name: str, items: List[yattag.doc.Doc]) -> None:
    """Generates the 'existing house numbers/streets' part of the header."""
    prefix = config.Config.get_uri_prefix()
    if streets != "only":
        doc = yattag.doc.Doc()
        with doc.tag("a", href=prefix + "/street-housenumbers/" + relation_name + "/view-result"):
            doc.text(_("Existing house numbers"))
        items.append(doc)

    doc = yattag.doc.Doc()
    with doc.tag("a", href=prefix + "/streets/" + relation_name + "/view-result"):
        doc.text(_("Existing streets"))
    items.append(doc)


def get_toolbar(
        relations: Optional[areas.Relations] = None,
        function: str = "",
        relation_name: str = "",
        relation_osmid: int = 0
) -> yattag.doc.Doc:
    """Produces the start of the page. Note that the content depends on the function and the
    relation, but not on the action to keep a balance between too generic and too specific
    content."""
    items: List[yattag.doc.Doc] = []

    if relations and relation_name:
        relation = relations.get_relation(relation_name)
        streets = relation.get_config().should_check_missing_streets()

    doc = yattag.doc.Doc()
    prefix = config.Config.get_uri_prefix()
    with doc.tag("a", href=prefix + "/"):
        doc.text(_("Area list"))
    items.append(doc)

    if relation_name:
        fill_missing_header_items(streets, relation_name, items)

    fill_header_function(function, relation_name, items)

    if relation_name:
        fill_existing_header_items(streets, relation_name, items)

    if function in ("missing-housenumbers", "missing-streets"):
        doc = yattag.doc.Doc()
        with doc.tag("a", href="https://overpass-turbo.eu/"):
            doc.text(_("Overpass turbo"))
        items.append(doc)

    if relation_osmid:
        doc = yattag.doc.Doc()
        with doc.tag("a", href="https://www.openstreetmap.org/relation/" + str(relation_osmid)):
            doc.text(_("Area boundary"))
        items.append(doc)

    doc = yattag.doc.Doc()
    with doc.tag("a", href=prefix + "/housenumber-stats/hungary/"):
        doc.text(_("Statistics"))
    items.append(doc)

    doc = yattag.doc.Doc()
    with doc.tag("a", href="https://github.com/vmiklos/osm-gimmisn/tree/master/doc"):
        doc.text(_("Documentation"))
    items.append(doc)

    doc = yattag.doc.Doc()
    with doc.tag("div", id="toolbar"):
        for index, item in enumerate(items):
            if index:
                doc.text(" ¦ ")
            doc.asis(item.getvalue())
    doc.stag("hr")
    return doc


def handle_static(request_uri: str) -> Tuple[str, str]:
    """Handles serving static content."""
    tokens = request_uri.split("/")
    path = tokens[-1]

    if request_uri.endswith(".js"):
        content_type = "application/x-javascript"
    elif request_uri.endswith(".css"):
        content_type = "text/css"
    elif request_uri.endswith(".json"):
        content_type = "application/json"

    if path.endswith(".js") or path.endswith(".css"):
        prefix = config.Config.get_uri_prefix()
        template = util.get_content(config.get_abspath("static"), path)
        content = template.replace("@PREFIX@", prefix)
        return content, content_type
    if path.endswith(".json"):
        return util.get_content(os.path.join(config.Config.get_workdir(), "stats"), path), content_type

    return "", ""


def send_response(
        start_response: 'StartResponse',
        content_type: str,
        status: str,
        output: str,
        extra_headers: List[Tuple[str, str]]
) -> Iterable[bytes]:
    """Turns an output string into a byte array and sends it."""
    output_bytes = output.encode('utf-8')
    if content_type != "application/octet-stream":
        content_type += "; charset=utf-8"
    response_headers = [('Content-type', content_type),
                        ('Content-Length', str(len(output_bytes)))]
    response_headers += extra_headers
    start_response(status, response_headers)
    return [output_bytes]


def handle_exception(
        environ: Dict[str, Any],
        start_response: 'StartResponse'
) -> Iterable[bytes]:
    """Displays an unhandled exception on the page."""
    status = '500 Internal Server Error'
    path_info = environ.get("PATH_INFO")
    request_uri = path_info
    doc = yattag.doc.Doc()
    util.write_html_header(doc)
    with doc.tag("pre"):
        doc.text(_("Internal error when serving {0}").format(request_uri) + "\n")
        doc.text(traceback.format_exc())
    return send_response(start_response, "text/html", status, doc.getvalue(), [])


def local_to_ui_tz(local_dt: datetime.datetime) -> datetime.datetime:
    """Converts from local date-time to UI date-time, based on config."""
    if config.Config.has_value("timezone"):
        ui_tz = pytz.timezone(config.Config.get_timezone())
    else:
        ui_tz = pytz.timezone("Europe/Budapest")

    return local_dt.astimezone(ui_tz)


def format_timestamp(timestamp: float) -> str:
    """Formats timestamp as UI date-time."""
    local_dt = datetime.datetime.fromtimestamp(timestamp)
    ui_dt = local_to_ui_tz(local_dt)
    fmt = '%Y-%m-%d %H:%M'
    return ui_dt.strftime(fmt)


def handle_stats(relations: areas.Relations, _request_uri: str) -> yattag.doc.Doc:
    """Expected request_uri: e.g. /osm/housenumber-stats/hungary/."""
    doc = yattag.doc.Doc()
    doc.asis(get_toolbar(relations).getvalue())

    prefix = config.Config.get_uri_prefix()
    with doc.tag("script", src=prefix + "/static/Chart.min.js"):
        pass
    with doc.tag("script", src=prefix + "/static/chartjs-plugin-datalabels.min.js"):
        pass
    with doc.tag("script", src=prefix + "/static/chartjs-plugin-trendline.min.js"):
        pass
    with doc.tag("script", src=prefix + "/static/stats.js"):
        pass

    # Emit localized strings for JS purposes.
    with doc.tag("div", style="display: none;"):
        string_pairs = [
            ("str-daily-title", _("New house numbers, last 2 weeks, as of {}")),
            ("str-daily-x-axis", _("During this day")),
            ("str-daily-y-axis", _("New house numbers")),
            ("str-monthly-title", _("New house numbers, last year, as of {}")),
            ("str-monthly-x-axis", _("During this month")),
            ("str-monthly-y-axis", _("New house numbers")),
            ("str-monthlytotal-title", _("All house numbers, last year, as of {}")),
            ("str-monthlytotal-x-axis", _("Latest for this month")),
            ("str-monthlytotal-y-axis", _("All house numbers")),
            ("str-dailytotal-title", _("All house numbers, last 2 weeks, as of {}")),
            ("str-dailytotal-x-axis", _("At the start of this day")),
            ("str-dailytotal-y-axis", _("All house numbers")),
            ("str-topusers-title", _("Top house number editors, as of {}")),
            ("str-topusers-x-axis", _("User name")),
            ("str-topusers-y-axis", _("Number of house numbers last changed by this user")),
            ("str-topcities-title", _("Top edited cities, as of {}")),
            ("str-topcities-x-axis", _("City name")),
            ("str-topcities-y-axis", _("Number of house numbers added in the past 30 days")),
            ("str-usertotal-title", _("Number of house number editors, as of {}")),
            ("str-usertotal-x-axis", _("All editors")),
            ("str-usertotal-y-axis", _("Number of editors, at least one housenumber is last changed by these users")),
            ("str-progress-title", _("Coverage is {1}%, as of {2}")),
            ("str-progress-x-axis", _("Number of house numbers in database")),
            ("str-progress-y-axis", _("Data source")),
        ]
        for key, value in string_pairs:
            kwargs: Dict[str, str] = {}
            kwargs["id"] = key
            kwargs["data-value"] = value
            with doc.tag("div", **kwargs):
                pass

    title_ids = [
        (_("New house numbers"), "daily"),
        (_("All house numbers"), "dailytotal"),
        (_("New house numbers, monthly"), "monthly"),
        (_("All house numbers, monthly"), "monthlytotal"),
        (_("Top house number editors"), "topusers"),
        (_("Top edited cities"), "topcities"),
        (_("All house number editors"), "usertotal"),
        (_("Coverage"), "progress"),
    ]

    with doc.tag("ul"):
        for title, identifier in title_ids:
            with doc.tag("li"):
                with doc.tag("a", href="#_" + identifier):
                    doc.text(title)

    for title, identifier in title_ids:
        with doc.tag("h2", id="_" + identifier):
            doc.text(title)
        with doc.tag("div", klass="canvasblock"):
            with doc.tag("canvas", id=identifier):
                pass

    with doc.tag("h2"):
        doc.text(_("Note"))
    with doc.tag("div"):
        doc.text(_("""These statistics are provided purely for interested editors, and are not
intended to reflect quality of work done by any given editor in OSM. If you want to use
them to motivate yourself, that's fine, but keep in mind that a bit of useful work is
more meaningful than a lot of useless work."""))

    doc.asis(get_footer().getvalue())
    return doc


def get_request_uri(environ: Dict[str, Any], relations: areas.Relations) -> str:
    """Finds out the request URI."""
    request_uri = cast(str, environ.get("PATH_INFO"))

    prefix = config.Config.get_uri_prefix()
    if request_uri:
        # Compatibility.
        if request_uri.startswith(prefix + "/suspicious-streets/"):
            request_uri = request_uri.replace('suspicious-streets', 'missing-housenumbers')
        elif request_uri.startswith(prefix + "/suspicious-relations/"):
            request_uri = request_uri.replace('suspicious-relations', 'missing-streets')

        # Performance: don't bother with relation aliases for non-relation requests.
        if not request_uri.startswith(prefix + "/streets/") \
                and not request_uri.startswith(prefix + "/missing-streets/") \
                and not request_uri.startswith(prefix + "/street-housenumbers/") \
                and not request_uri.startswith(prefix + "/missing-housenumbers/"):
            return request_uri

        # Relation aliases.
        aliases = relations.get_aliases()
        tokens = request_uri.split("/")
        relation_name = tokens[-2]
        if relation_name in aliases:
            request_uri = request_uri.replace(relation_name, aliases[relation_name])

    return request_uri


def check_existing_relation(relations: areas.Relations, request_uri: str) -> yattag.doc.Doc:
    """Prevents serving outdated data from a relation that has been renamed."""
    doc = yattag.doc.Doc()
    prefix = config.Config.get_uri_prefix()
    if not request_uri.startswith(prefix + "/streets/") \
            and not request_uri.startswith(prefix + "/missing-streets/") \
            and not request_uri.startswith(prefix + "/street-housenumbers/") \
            and not request_uri.startswith(prefix + "/missing-housenumbers/"):
        return doc

    tokens = request_uri.split("/")
    relation_name = tokens[-2]
    if relation_name in relations.get_names():
        return doc

    with doc.tag("div", id="no-such-relation-error"):
        doc.text(_("No such relation: {0}").format(relation_name))
    return doc


# vim:set shiftwidth=4 softtabstop=4 expandtab:
