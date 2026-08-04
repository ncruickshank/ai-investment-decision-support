# src / ingestion / documents / parser.py
from pathlib import Path
from bs4 import BeautifulSoup, Comment
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