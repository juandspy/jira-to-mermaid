#!/usr/bin/env python

import csv
from enum import Enum
from typing import List
from dataclasses import dataclass
import argparse


DEFAULT__ISSUE_FILEPATH = "issues.csv"
DEFAULT__IGNORE_LINKS = ["Cloners"]

# To be overwritten by args
DEFAULT__TASK__SHAPE_LEFT     = "["
DEFAULT__TASK__SHAPE_RIGHT    = "]"
DEFAULT__BUG__SHAPE_LEFT      = "(("
DEFAULT__BUG__SHAPE_RIGHT     = "))"
DEFAULT__SPIKE__SHAPE_LEFT    = "{"
DEFAULT__SPIKE__SHAPE_RIGHT   = "}"
DEFAULT__DEFAULT__SHAPE_LEFT  = "("
DEFAULT__DEFAULT__SHAPE_RIGHT = ")"

DEFAULT__TODO__COLOR        = "#ff9933"
DEFAULT__CLOSED__COLOR      = "#33cc33"
DEFAULT__IN_PROGRESS__COLOR = "#33ccff"
DEFAULT__CODE_REVIEW__COLOR = "#ffff66"
DEFAULT__REVIEW__COLOR      = "#ffcc00"
DEFAULT__DEFAULT__COLOR     = "#f9f"

DEFAULT__GRAPH_DIRECTION = "TD"

class IssueType(Enum):
    """The Issue type."""
    EPIC = "Epic"
    STORY = "Story"
    TASK = "Task"
    BUG = "Bug"
    SPIKE = "Spike"


class IssueStatus(Enum):
    """The Issue status."""
    TODO = "To Do"
    CLOSED = "Closed"
    IN_PROGRESS = "In Progress"
    CODE_REVIEW = "Code Review"
    REVIEW = "Review"

def jira_key_to_mermaid_id(key: str) -> str:
    """Replaces the - as it cannot be part of the mermaid ID."""
    return key.replace("-", "_")

@dataclass
class Link:
    key: str
    kind: str

def get_link_kind_from_header(header: str) -> str:
    """Get the link type e.g. 'Inward issue link (Blocks)' -> 'Blocks'"""
    return header[header.find("(")+1:header.find(")")]

class Issue:
    def __init__(
        self,
        key: str,
        kind: IssueType,
        status: IssueStatus,
        summary: str,
        out_links: List[Link] = [],
        in_links: List[Link] = [],
        shape_left: str = DEFAULT__DEFAULT__SHAPE_LEFT,
        shape_right: str = DEFAULT__DEFAULT__SHAPE_RIGHT):
        """Initialize the issue."""
        self.key = key
        self.kind = kind
        self.status = status
        self.summary = summary
        self.out_links = out_links
        self.in_links = in_links
        self.shape_left = shape_left
        self.shape_right = shape_right

    def __repr__(self):
        """Useful for debugging."""
        out = f"Issue(key={self.key}, kind={self.kind}, status={self.status}, summary={self.summary} "
        out += f"out_links={self.out_links} " if len(self.out_links) > 0 else ""
        out += f"in_links={self.in_links}) " if len(self.in_links) > 0 else ""
        return out

    def to_mermaid_node(self) -> str:
        """Renders the issue as a mermaid node."""
        cleaned_summary = self.summary.replace('"', "'")
        out = f"{jira_key_to_mermaid_id(self.key)}"
        out += f"{self.shape_left}\"{self.key} ({self.status.value})\\n{cleaned_summary}\"{self.shape_right}"
        out += f":::{self.status.name}" # add the styling class
        return out

def csv_row_to_issue(
        row, header,
        task__shape_left: str     = DEFAULT__TASK__SHAPE_LEFT,
        task__shape_right: str    = DEFAULT__TASK__SHAPE_RIGHT,
        bug__shape_left: str      = DEFAULT__BUG__SHAPE_LEFT,
        bug__shape_right: str     = DEFAULT__BUG__SHAPE_RIGHT,
        spike__shape_left: str    = DEFAULT__SPIKE__SHAPE_LEFT,
        spike__shape_right: str   = DEFAULT__SPIKE__SHAPE_RIGHT,
        default__shape_left: str  = DEFAULT__DEFAULT__SHAPE_LEFT,
        default__shape_right: str = DEFAULT__DEFAULT__SHAPE_RIGHT):
    """Parse a CSV of Jira issues into a list of Issues."""
    out_links = [Link(key=val,kind=get_link_kind_from_header(col))
                 for col, val in zip(header, row) if "Outward" in col and val != ""]
    in_links = [Link(key=val,kind=get_link_kind_from_header(col))
                for col, val in zip(header, row) if "Inward" in col and val != ""]
    kind = IssueType(row[header.index("Issue Type")])
    match kind:
        case IssueType.TASK:
            shape_left = task__shape_left
            shape_right = task__shape_right
        case IssueType.BUG:
            shape_left = bug__shape_left
            shape_right = bug__shape_right
        case IssueType.SPIKE:
            shape_left = spike__shape_left
            shape_right = spike__shape_right
        case _:
            shape_left = default__shape_left
            shape_right = default__shape_right
    return Issue(
        key=row[header.index("Issue key")],
        kind=kind,
        status=IssueStatus(row[header.index("Status")]),
        summary=row[header.index("Summary")],
        out_links=out_links,
        in_links=in_links,
        shape_left=shape_left,
        shape_right=shape_right
    )

def generate_mermaid_code(
        issues: List[Issue], ignore_links: List[str] = [],
        graph_direction: str = DEFAULT__GRAPH_DIRECTION,
        todo__color: str = DEFAULT__TODO__COLOR,
        closed__color: str = DEFAULT__CLOSED__COLOR,
        in_progress__color: str = DEFAULT__IN_PROGRESS__COLOR,
        code_review__color: str = DEFAULT__CODE_REVIEW__COLOR,
        review__color: str = DEFAULT__REVIEW__COLOR,
        default__color: str = DEFAULT__DEFAULT__COLOR) -> str:
    """Generate the mermaid code by rendering the issues and adding some styling."""
    mermaid_code = f"graph {graph_direction};\n"

    for issue in issues:
        mermaid_code += f"\t{issue.to_mermaid_node()}\n"

        for out_link in issue.out_links:
            if out_link.kind not in ignore_links:
                mermaid_code += f"\t{jira_key_to_mermaid_id(issue.key)} "
                mermaid_code += f"-- {out_link.kind} --> " if out_link.kind else " --> "
                mermaid_code += f"{jira_key_to_mermaid_id(out_link.key)}\n"

        for in_link in issue.in_links:
            if in_link.kind not in ignore_links:
                mermaid_code += f"\t{jira_key_to_mermaid_id(in_link.key)} "
                mermaid_code += f"-- {in_link.kind} --> " if in_link.kind else " --> "
                mermaid_code += f"{jira_key_to_mermaid_id(issue.key)}\n"


    mermaid_code += f"""
    classDef TODO fill:{todo__color}
    classDef CLOSED fill:{closed__color}
    classDef IN_PROGRESS fill:{in_progress__color}
    classDef CODE_REVIEW fill:{code_review__color}
    classDef REVIEW fill:{review__color}
    classDef default fill:{default__color},stroke:#333,stroke-width:4px;"""
    return mermaid_code


def main():
    parser = argparse.ArgumentParser(
        description="Generate Mermaid code from a Jira CSV file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--csv_file", default=DEFAULT__ISSUE_FILEPATH, help="Path to the Jira CSV file")
    parser.add_argument("--ignore_links", default=DEFAULT__IGNORE_LINKS, help="Links to ignore")

    parser.add_argument(
        "--task__shape_left", 
        default=DEFAULT__TASK__SHAPE_LEFT,
        help="The task node's left shape")
    parser.add_argument(
        "--task__shape_right", 
        default=DEFAULT__TASK__SHAPE_RIGHT,
        help="The task node's right shape")
    parser.add_argument(
        "--bug__shape_left", 
        default=DEFAULT__BUG__SHAPE_LEFT,
        help="The bug node's left shape")
    parser.add_argument(
        "--bug__shape_right", 
        default=DEFAULT__BUG__SHAPE_RIGHT,
        help="The bug node's right shape")
    parser.add_argument(
        "--spike__shape_left", 
        default=DEFAULT__SPIKE__SHAPE_LEFT,
        help="The spike node's left shape")
    parser.add_argument(
        "--spike__shape_right", 
        default=DEFAULT__SPIKE__SHAPE_RIGHT,
        help="The spike node's right shape")
    parser.add_argument(
        "--default__shape_left", 
        default=DEFAULT__DEFAULT__SHAPE_LEFT,
        help="The default node's left shape")
    parser.add_argument(
        "--default__shape_right", 
        default=DEFAULT__DEFAULT__SHAPE_RIGHT,
        help="The default node's right shape when the task is not a task, spike or bug")

    parser.add_argument(
        "--todo__color",
        default=DEFAULT__TODO__COLOR,
        help="The TODO node color")
    parser.add_argument(
        "--closed__color",
        default=DEFAULT__CLOSED__COLOR,
        help="The CLOSED node color")
    parser.add_argument(
        "--in_progress__color",
        default=DEFAULT__IN_PROGRESS__COLOR,
        help="The IN PROGRESS node color")
    parser.add_argument(
        "--code_review__color",
        default=DEFAULT__CODE_REVIEW__COLOR,
        help="The CODE REVIEW node color")
    parser.add_argument(
        "--review__color",
        default=DEFAULT__REVIEW__COLOR,
        help="The REVIEW node color")
    parser.add_argument(
        "--default__color", 
        default=DEFAULT__DEFAULT__COLOR,
        help="The default node color")

    parser.add_argument(
        "--graph_direction", 
        default=DEFAULT__GRAPH_DIRECTION,
        help="The graph direction. Must be one of 'TD' or 'LR'")

    args = parser.parse_args()

    if args.graph_direction not in ['TD', 'LR']:
        raise ValueError(f"graph_direction must be one of 'TD' or 'LR', got{args.graph_direction}")    

    issues: List[Issue] = []

    with open(args.csv_file, newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile, quotechar='"', delimiter=",", skipinitialspace=False)
        header = next(reader)  # Skip the header row
        header = [x.strip() for x in header]
        for row in reader:
            row = [x.strip() for x in row]
            issues.append(csv_row_to_issue(
                row, header,
                task__shape_left     = args.task__shape_left,
                task__shape_right    = args.task__shape_right,
                bug__shape_left      = args.bug__shape_left,
                bug__shape_right     = args.bug__shape_right,
                spike__shape_left    = args.spike__shape_left,
                spike__shape_right   = args.spike__shape_right,
                default__shape_left  = args.default__shape_left,
                default__shape_right = args.default__shape_right))

    code = generate_mermaid_code(
        issues, args.ignore_links, args.graph_direction,
        todo__color         = args.todo__color,
        closed__color       = args.closed__color,
        in_progress__color  = args.in_progress__color,
        code_review__color  = args.code_review__color,
        review__color       = args.review__color,
        default__color      = args.default__color)
    print(code)

if __name__ == "__main__":
    main()
