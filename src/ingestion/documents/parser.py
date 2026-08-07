# src / ingestion / documents / parser.py
from pathlib import Path
from bs4 import BeautifulSoup, Comment, Tag
import re

from .sec import FilingMetadata

class DocumentMetadata:
    company: str
    ticker: str
    cik: str
    filing_type: str
    filing_date: str
    period_start: str 
    period_end: str 
    accession_number: str
    source: str 
    raw_html_path: str 

class Paragraph:
    text: str 

class Table:
    caption: str
    headers: str
    rows: list[list[str]]

class Section:
    part: str 
    item: str 
    title: str
    blocks: list[Paragraph | Table]

class Document:
    metadata: DocumentMetadata
    sections: list[Section]

class DocumentParser:
    """ 
    Description
    ----------
    This class contains the methods necessary to restructure an HTML
    file into a highly structured text class ready for downstream
    RAG processing.

    NOTE
    - self.metadata.period_start and self.metadata.period_end may have
      variable date formatting.
    """
    def __init__(self):
        super().__init__()

        # instantiate objects to be created later
        self.html_path = None
        self.soup = None
        self.metadata = DocumentMetadata()

    # =======================
    # === Public Methods  ===
    # =======================

    def load_html(self, html_path: str):
        """
        Description
        ----------
        Loads the html file from the given path and returns a BeautifulSoup object.

        Inputs
        ----------
        html_path = The path to the HTML file to be loaded

        Returns
        ----------
        BeautifulSoup object of the loaded HTML file stored in self.soup
        """
        # store the path for later use
        self.html_path = Path(html_path)

        # read the html
        with open(html_path, 'r', encoding = 'utf-8') as f:
            html = f.read()

        self.soup = BeautifulSoup(html, 'html.parser')

        # store metadata attributes before proceeding to cleaning

        ## company name
        self.metadata.company = self._find_ix_value('dei:EntityRegistrantName')

        ## period reported
        context = self.soup.find("xbrli:context")
        start = self._find_ix_value("dei:DocumentPeriodStartDate")
        if start is not None:
            self.metadata.period_start = start 
        else:
            self.metadata.period_start = context.find("xbrli:startdate").get_text(strip = True)
            
        end = self._find_ix_value("dei:DocumentPeriodEndDate")
        if end is not None:
            self.metadata.period_end = end 
        else:
            self.metadata.period_end = context.find("xbrli:enddate").get_text(strip = True)

    def clean_dom(self):
        """
        Description
        ----------
        Removes the HTML elements that do not pertain to the semantic content
        of the document.

        NOTE: This method only removes things that are always safe to remove.

        Inputs
        ----------
        None

        Returns
        ----------
        None. self.soup is modified in place.
        """
        if self.soup is None:
            raise ValueError("HTML document not loaded. Please call load_html() first.")

        # --- Remove Javascript and CSS ---
        for tag in self.soup.find_all(['script', 'style']):
            tag.decompose()

        # --- Remove HTML comments ---
        for comment in self.soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.decompose()

        # --- Remove hidden elements ---
        for tag in self.soup.find_all(style = True):
            style = tag['style'].replace(' ', '').lower()
            if (
                'display:none' in style or 
                'visibility:hidden' in style or 
                'opacity:0' in style
            ):
                tag.decompose()

        # --- Remove anchor tags, but preserve content ---
        for tag in self.soup.find_all('a'):
            tag.unwrap()

        # --- Remove inline XBRL wrappers while preserving text ---
        for tag in self.soup.find_all():
            if ':' in tag.name:
                prefix = tag.name.split(":")[0]
                if prefix in {'ix', 'ixt', 'ixt-sec'}:
                    tag.unwrap()

        # --- Remove empty tags ---
        for tag in self.soup.find_all():
            if (
                tag.name not in {'br', 'hr'} and 
                not tag.get_text(strip = True) and 
                not tag.find('table')
            ):
                tag.decompose()

    def extract_metadata(
        self,
        filing_metadata: FilingMetadata,
        ticker: str,
        source: str = 'SEC EDGAR'
    ):
        """
        Description
        ----------
        This method builds the metadata for the document based on
        previously known information within the production pipeline
        and information we must extract from the self.soup

        Inputs
        ----------
        filing_metadata = The FilingMetadata object created as part of 
            retrieving the document from the SEC EDGAR database
        ticker = The ticker for the company
        source = The source of the data. Defaults to 'SEC EDGAR'
        """
        # --- populate metadata with already known info ---

        ## define attributes already known by DocumentParser
        self.metadata.raw_html_path = self.html_path
        
        ## define attributes already known from the filing
        self.metadata.cik = filing_metadata.cik
        self.metadata.accession_number = filing_metadata.accession_number
        self.metadata.filing_type = filing_metadata.filing_type
        self.metadata.filing_date = filing_metadata.filing_date

        ## define attributes known other provided params
        self.metadata.ticker = ticker
        self.metadata.source = source

        # --- extract the rest of the info needed for metadata ---

    def remove_boilerplate(self):
        """
        Description
        ----------
        This method removes all the boilerplate content within the
        filing which we can safely determine does not carry 
        unique semantic meaning.

        Removes:
        - Repeated page headers
        - Table of contents
        - Page-number footers
        - HTML page-break elements
        - Empty structural elements

        Preserves:
        - Narative text
        - Section headings
        - Financial tables
        - Lists
        - Other semantically meaningful document content

        Inputs
        ----------

        Returns
        ----------
        None, but self.soup will be updated in place. 
        """
        if self.soup is None:
            raise RuntimeError('No HTML has been loaded.')

        # --- remove page headers ---
        for table in self.soup.find_all('table'):
            text = table.get_text(' ', strip = True)

            if text.lower() in {
                self.metadata.company.lower(),
                re.sub(r'\s(inc|llc|org)(\.)?', '', self.metadata.company.lower())
            }:
                table.decompose()

        # --- remove table of contents ---
        for table in self.soup.find_all('table'):
            text = table.get_text(' ', strip = True).lower()

            if (
                'table of contents' in text and 
                'signatures' in text and 
                len(text) > 500
            ):
                table.decompose()

        # --- remove page break elements ---
        for tag in self.soup.find_all('hr'):
            tag.decompose()

        # --- remove page-number containers ---
        for tag in self.soup.find_all(
            'div',
            style = lambda value: value and 'position:absolute' in value.lower()
        ):
            text = tag.get_text(' ', strip = True)

            if text.isdigit():
                tag.decompose()

        # --- remove now-empty structural elements ---
        for tag in self.soup.find_all():
            if (
                tag.name not in {'br', 'hr'} and 
                not tag.get_text(strip = True) and 
                not tag.find(['table', 'img'])
            ):
                tag.decompose()

    def extract_sections(self):
        """
        Description
        ----------
        Identify the major Part/Item sections in the filing.

        Sections are idenifited from the visible text of the DOM elements.
        This method does not modify self.soup.

        NOTE: This only returns *boundaries* of sections. Not the 
        actual contents.

        Inputs
        ----------
        None

        Returns
        ----------
        list[dict]
            A list of section boundary records. Each record contains:
            - part: Filing part (e.g. "Part 1")
            - item: Item number (e.g. "Item 1")
            - title: Human-readable section title
            - element: BeautifulSoup Tag containing the section heading
        """
        if self.soup is None:
            raise RuntimeError('No HTML bas been loaded.')

        self.sections = []
        current_part = None 

        # ----------
        # SEC filings use a relatively consistent "PART 1." / "ITEM 1."
        # convention. We inspect block-level dics instead of all text
        # to ensure that references to these elements within the text 
        # are preserved.
        # ----------
        for element in self.soup.find_all(['div', 'p', 'h1', 'h2', 'h3']):
            text = element.get_text(' ', strip = True)

            if not text:
                continue

            ## --- detect part headings ---
            part_match = re.match(
                # r'^PART\s+(I{1,3}|IV)\.',
                r"^PART\s+(I{1,3}|IV)\.",
                text,
                flags = re.IGNORECASE 
            )
            # print(f'Part = {part_match}')

            if part_match:
                current_part = f"Part {part_match.group(1).upper()}"
                continue 

            ## --- detect item headings ---
            ## e.g. ITEM 1., ITEM 1A., ITEM 2.
            # if not self._is_section_heading(element):
            #     continue 

            item_match = re.match(
                # r'^(ITEM\s+\d+[A-Z]?)\.?\s*(.*)$',
                r"^(ITEM\s+\d+[A-Z]?)\.?\s*(.*)$",
                text,
                flags = re.IGNORECASE 
            )
            # print(f'Item = {item_match}')

            if item_match is None:
                continue

            if current_part is None:
                continue 

            self.sections.append(
                {
                    'part': current_part,
                    'item': item_match.group(1).upper(),
                    'title': item_match.group(2).strip(),
                    'element': element
                }
            )

    def html_to_blocks(self):
        raise NotImplementedError

    def split_into_sections(self):
        raise NotImplementedError

    def build_document(self):
        raise NotImplementedError

    # =======================
    # === Private Methods ===
    # =======================

    def _find_ix_value(self, name: str) -> str | None:
        tag = self.soup.find(attrs = {'name': name})

        if tag is None:
            return None 

        return tag.get_text(strip = True)

    def _is_section_heading(self, element: Tag) -> bool:
        """
        Determine whether a DOM element represents a major SEC
        Part/Item heading.
        """

        text = element.get_text(" ", strip=True)

        if not text:
            return False

        # A section heading should begin with ITEM.
        if not re.match(r"^ITEM\s+\d+[A-Z]?\.", text, re.IGNORECASE):
            return False

        # The Workiva filing renders major headings in bold.
        # Avoid classifying ordinary prose containing "Item X."
        # as a section heading.
        style = element.get("style", "").lower()

        if "font-weight:700" not in style:
            return False

        return True