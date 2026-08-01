# src / ingestion / documents / sec.py

"""
Contains the methodology by which we retrieve SEC Filings from the 
SEC EDGAR Database
"""
@dataclass
class FilingMetadata:
    ticker: str
    cik: str
    accession_number: str
    filing_type: str
    filing_date: date
    primary_document: str
    primary_doc_description: str
    filing_url: str

class SecEdgarProvider:
    """ 
    A class that provides methods to retrieve SEC filings from the SEC EDGAR Database.
    """

    def __init__(self):
        """
        Initializes the SecEdgarProvider class.
        """
        super().__init__()

    # ======================
    # === Public Methods ===
    # ======================

    def get_company_submissions(self, ticker:str) -> dict:
        """
        Description
        ----------
        Retrieves the company submissions for a given ticker symbol from the SEC EDGAR Database.

        Inputs
        ----------
        ticker (str): The ticker symbol of the company.

        Returns
        ----------

        """

    def list_filings(
        self,
        ticker: str,
        filing_types: list[str] | None = None,
        limit: int | None = None
    ) -> list[FilingMetaData]:
        """
        Description
        ----------
        Lists the filings available in the SEC EDGAR Database.

        Returns
        ----------
        list[FilingMetaData]: A list of FilingMetaData objects representing the available filings.
        """

    def download_filing(
        self,
        filing: FilingMetaData
    ) -> str:
        """
        Description
        ----------
        Downloads a specific filing from the SEC EDGAR Database.

        Inputs
        ----------
        filing (FilingMetaData): The FilingMetaData object representing the filing to be downloaded.

        Returns
        ----------
        str: The content of the downloaded filing as a string.
        """

    def download_primary_document(
        self,
        filing: FilingMetaData,
        output_path: Path
    ) -> Path:
        """
        Description
        ----------
        Downloads the primary document of a specific filing from the SEC EDGAR Database.

        Inputs
        ----------
        filing (FilingMetaData): The FilingMetaData object representing the filing.
        output_path (Path): The path where the primary document will be saved.

        Returns
        ----------
        """

    # =======================
    # === Private Methods ===
    # =======================

    def _get_cik(self):
        raise NotImplementedError("This method should be implemented to retrieve the CIK for a given ticker.")

    def _build_submission_url(self):
        raise NotImplementedError("This method should be implemented to build the submission URL for a given CIK.")

    def _build_filing_url(self):
        raise NotImplementedError("This method should be implemented to build the filing URL for a given filing.")

    def _request_json(self):
        raise NotImplementedError("This method should be implemented to make a JSON request to the SEC EDGAR Database.")

    def _request_text(self):
        raise NotImplementedError("This method should be implemented to make a text request to the SEC EDGAR Database.")
