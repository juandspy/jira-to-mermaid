#!/usr/bin/env python

import csv
from enum import Enum
from typing import List
from dataclasses import dataclass
import argparse


class IssueType(Enum):
    EPIC = "Epic"
    STORY = "Story"
    TASK = "Task"
    BUG = "Bug"
    SPIKE = "Spike"


class IssueStatus(Enum):
    TODO = "To Do"
    CLOSED = "Closed"
    IN_PROGRESS = "In Progress"
    CODE_REVIEW = "Code Review"
    REVIEW = "Review"


def jira_key_to_mermaid_id(key: str) -> str:
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
    ):
        self.key = key
        self.kind = kind
        self.status = status
        self.summary = summary
        self.out_links = out_links
        self.in_links = in_links

    def __repr__(self):
        out = f"Issue(key={self.key}, kind={self.kind}, status={self.status}, summary={self.summary} "
        out += f"out_links={self.out_links} " if len(self.out_links) > 0 else ""
        out += f"in_links={self.in_links}) " if len(self.in_links) > 0 else ""
        return out

    def to_mermaid_node(self) -> str:
        # TODO: color by kind
        match self.kind:
            case IssueType.TASK:
                shape_left = "["
                shape_right = "]"
            case IssueType.BUG:
                shape_left = "(("
                shape_right = "))"
            case IssueType.SPIKE:
                shape_left = "{"
                shape_right = "}"
            case _:
                shape_left = "("
                shape_right = ")"
        cleaned_summary = self.summary.replace('"', "'")
        
        out = f"{jira_key_to_mermaid_id(self.key)}"
        out += f"{shape_left}\"{self.key} ({self.status})\\n{cleaned_summary}\"{shape_right}"
        out += f":::{self.status.name}" # add the styling class
        return out


# Function to convert CSV rows to Issue instances
def csv_row_to_issue(row, header):
    out_links = [Link(key=val,kind=get_link_kind_from_header(col)) for col, val in zip(header, row) if "Outward" in col and val != ""]
    in_links = [Link(key=val,kind=get_link_kind_from_header(col)) for col, val in zip(header, row) if "Inward" in col and val != ""]
    return Issue(
        key=row[header.index("Issue key")],
        kind=IssueType(row[header.index("Issue Type")]),
        status=IssueStatus(row[header.index("Status")]),
        summary=row[header.index("Summary")],
        out_links=out_links,
        in_links=in_links,
    )

def generate_mermaid_code(issues: List[Issue], ignore_links = []) -> str:
    mermaid_code = "graph TD;\n"

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


    mermaid_code += """
    classDef TODO fill:#ff9933
    classDef CLOSED fill:#33cc33
    classDef IN_PROGRESS fill:#33ccff
    classDef CODE_REVIEW fill:#ffff66
    classDef REVIEW fill:#ffcc00"""
    return mermaid_code


def main():
    parser = argparse.ArgumentParser(description="Generate Mermaid code from a Jira CSV file.")
    parser.add_argument("--csv_file", default="issues.csv", help="Path to the Jira CSV file. Default is 'issues.csv'")
    parser.add_argument("--ignore_links", nargs="*", default=["Cloners"], help="Links to ignore. Default is '[Cloners]'")

    args = parser.parse_args()

    issues: List[Issue] = []

    with open(args.csv_file, newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile, quotechar='"', delimiter=",", skipinitialspace=False)
        header = next(reader)  # Skip the header row
        header = [x.strip() for x in header]
        for row in reader:
            row = [x.strip() for x in row]
            issues.append(csv_row_to_issue(row, header))

    code = generate_mermaid_code(issues, args.ignore_links)
    print(code)

if __name__ == "__main__":
    main()
