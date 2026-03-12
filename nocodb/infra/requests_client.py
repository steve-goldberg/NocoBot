import base64
import warnings
from typing import Optional, List, Dict, Any, Union
from ..core import (
    NocoDBClient,
    NocoDBBase,
    AuthToken,
    WhereFilter,
)
from ..api import NocoDBAPI
from ..utils import get_query_params
from ..exceptions import NocoDBAPIError

import requests


class NocoDBRequestsClient(NocoDBClient):
    def __init__(self, auth_token: AuthToken, base_uri: str, verify_ssl: bool = True):
        self.__session = requests.Session()
        self.__session.headers.update(
            auth_token.get_header(),
        )
        self.__session.headers.update({"Content-Type": "application/json"})
        self.__session.verify = verify_ssl  # For self-signed certs in homelab
        self.__api_info = NocoDBAPI(base_uri)

    def _request(self, method: str, url: str, *args, **kwargs):
        response = self.__session.request(method, url, *args, **kwargs)
        response_json = None
        try:
            response.raise_for_status()
            response_json = response.json()
        except requests.exceptions.JSONDecodeError:
            ...
        except requests.exceptions.HTTPError as http_error:
            raise NocoDBAPIError(
                message=str(http_error),
                status_code=http_error.response.status_code,
                response_json=response_json,
                response_text=response.text
            )

        return response

    # =========================================================================
    # v3 Data API Methods
    # =========================================================================

    def records_list_v3(
        self,
        base_id: str,
        table_id: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """List records using v3 API.

        GET /api/v3/data/{baseId}/{tableId}/records

        Args:
            base_id: The base (project) ID
            table_id: The table ID
            params: Optional query parameters:
                - fields: Comma-separated field names to include
                - sort: Sort field(s), prefix with - for descending
                - where: Filter condition
                - page: Page number (1-indexed)
                - pageSize: Number of records per page
                - viewId: Optional view ID to filter by

        Returns:
            Dict with 'records' array and optional 'next' pagination URL
            Example: {"records": [{"id": 1, "fields": {...}}], "next": "url"}
        """
        url = self.__api_info.get_records_uri(base_id, table_id)
        return self._request("GET", url, params=params).json()

    def record_get_v3(
        self,
        base_id: str,
        table_id: str,
        record_id: Union[int, str],
    ) -> Dict[str, Any]:
        """Get a single record using v3 API.

        GET /api/v3/data/{baseId}/{tableId}/records/{recordId}

        Args:
            base_id: The base (project) ID
            table_id: The table ID
            record_id: The record ID

        Returns:
            Dict with 'id' and 'fields'
            Example: {"id": 1, "fields": {"Name": "John", "Age": 30}}
        """
        url = self.__api_info.get_record_uri(base_id, table_id, str(record_id))
        return self._request("GET", url).json()

    def records_create_v3(
        self,
        base_id: str,
        table_id: str,
        records: Union[Dict[str, Any], List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        """Create one or more records using v3 API.

        POST /api/v3/data/{baseId}/{tableId}/records

        Args:
            base_id: The base (project) ID
            table_id: The table ID
            records: Single record dict or list of record dicts
                Each record should have a 'fields' key with field values
                Example: {"fields": {"Name": "John"}} or
                         [{"fields": {"Name": "John"}}, {"fields": {"Name": "Jane"}}]

        Returns:
            List of created records with 'id' and 'fields'
            Example: [{"id": 1, "fields": {"Name": "John"}}]
        """
        url = self.__api_info.get_records_uri(base_id, table_id)

        # Normalize to list format for API
        if isinstance(records, dict):
            body = [records]
        else:
            body = records

        result = self._request("POST", url, json=body).json()
        # v3 API returns {"records": [...]} wrapper
        return result.get("records", result)

    def records_update_v3(
        self,
        base_id: str,
        table_id: str,
        records: Union[Dict[str, Any], List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        """Update one or more records using v3 API.

        PATCH /api/v3/data/{baseId}/{tableId}/records

        Args:
            base_id: The base (project) ID
            table_id: The table ID
            records: Single record dict or list of record dicts
                Each record must have 'id' and 'fields' keys
                Example: {"id": 1, "fields": {"Name": "Updated"}} or
                         [{"id": 1, "fields": {...}}, {"id": 2, "fields": {...}}]

        Returns:
            List of updated records with 'id' and 'fields'
            Example: [{"id": 1, "fields": {"Name": "Updated"}}]
        """
        url = self.__api_info.get_records_uri(base_id, table_id)

        # Normalize to list format for API
        if isinstance(records, dict):
            body = [records]
        else:
            body = records

        result = self._request("PATCH", url, json=body).json()
        # v3 API returns {"records": [...]} wrapper
        return result.get("records", result)

    def records_delete_v3(
        self,
        base_id: str,
        table_id: str,
        record_ids: Union[int, str, List[Union[int, str]]],
    ) -> List[Dict[str, Any]]:
        """Delete one or more records using v3 API.

        DELETE /api/v3/data/{baseId}/{tableId}/records

        Args:
            base_id: The base (project) ID
            table_id: The table ID
            record_ids: Single record ID or list of record IDs to delete

        Returns:
            List of deleted record IDs
            Example: [{"id": 1}, {"id": 2}]
        """
        url = self.__api_info.get_records_uri(base_id, table_id)

        # Normalize to list format for API
        if isinstance(record_ids, (int, str)):
            body = [{"id": record_ids}]
        else:
            body = [{"id": rid} for rid in record_ids]

        result = self._request("DELETE", url, json=body).json()
        # v3 API returns {"records": [...]} wrapper
        return result.get("records", result)

    def records_count_v3(
        self,
        base_id: str,
        table_id: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, int]:
        """Get record count using v3 API.

        GET /api/v3/data/{baseId}/{tableId}/count

        Args:
            base_id: The base (project) ID
            table_id: The table ID
            params: Optional query parameters (e.g., where filter)

        Returns:
            Dict with 'count' key
            Example: {"count": 42}
        """
        url = self.__api_info.get_records_count_uri(base_id, table_id)
        return self._request("GET", url, params=params).json()

    def records_list_all_v3(
        self,
        base_id: str,
        table_id: str,
        params: Optional[Dict[str, Any]] = None,
        max_pages: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """List ALL records from a table, automatically handling pagination.

        This method fetches all pages of records from a table, following the
        'next' URL returned by the v3 API until no more pages are available.

        Args:
            base_id: The base (project) ID
            table_id: The table ID
            params: Optional query parameters (pageSize, where, sort, etc.)
            max_pages: Optional limit on pages to fetch (None = unlimited)

        Returns:
            List of all records (may be large!)
            Each record has 'id' and 'fields' keys.

        Example:
            all_users = client.records_list_all_v3(base_id, table_id, params={
                "pageSize": 100,
                "where": "(Status,eq,Active)"
            })
        """
        from ..utils import collect_all_v3

        def fetch(p: Dict[str, Any]) -> Dict[str, Any]:
            merged_params = dict(params or {})
            merged_params.update(p)
            return self.records_list_v3(base_id, table_id, params=merged_params)

        return collect_all_v3(fetch, params, max_pages)

    def linked_records_list_v3(
        self,
        base_id: str,
        table_id: str,
        link_field_id: str,
        record_id: Union[int, str],
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """List linked records for a specific record using v3 API.

        GET /api/v3/data/{baseId}/{tableId}/links/{linkFieldId}/{recordId}

        Args:
            base_id: The base (project) ID
            table_id: The table ID
            link_field_id: The link field ID
            record_id: The record ID
            params: Optional query parameters:
                - fields: Comma-separated field names to include
                - sort: Sort field(s), prefix with - for descending
                - where: Filter condition
                - page: Page number (1-indexed)
                - pageSize: Number of records per page

        Returns:
            Dict with linked records. Format varies by relationship type:
            - hm (has many): {"list": [...]} or {"records": [...]}
            - bt (belongs to): {"record": {...}} (singular)
            May include optional 'next' pagination URL for hm relationships.
        """
        url = self.__api_info.get_linked_records_uri(base_id, table_id, link_field_id, str(record_id))
        return self._request("GET", url, params=params).json()

    def linked_records_link_v3(
        self,
        base_id: str,
        table_id: str,
        link_field_id: str,
        record_id: Union[int, str],
        linked_record_ids: Union[int, str, List[Union[int, str]]],
    ) -> List[Dict[str, Any]]:
        """Link records to a specific record using v3 API.

        POST /api/v3/data/{baseId}/{tableId}/links/{linkFieldId}/{recordId}

        Args:
            base_id: The base (project) ID
            table_id: The table ID
            link_field_id: The link field ID
            record_id: The record ID to link to
            linked_record_ids: Single record ID or list of record IDs to link

        Returns:
            List of linked record references
            Example: [{"id": 1}, {"id": 2}]
        """
        url = self.__api_info.get_linked_records_uri(base_id, table_id, link_field_id, str(record_id))

        # Normalize to list format for API
        if isinstance(linked_record_ids, (int, str)):
            body = [{"id": linked_record_ids}]
        else:
            body = [{"id": rid} for rid in linked_record_ids]

        return self._request("POST", url, json=body).json()

    def linked_records_unlink_v3(
        self,
        base_id: str,
        table_id: str,
        link_field_id: str,
        record_id: Union[int, str],
        linked_record_ids: Union[int, str, List[Union[int, str]]],
    ) -> List[Dict[str, Any]]:
        """Unlink records from a specific record using v3 API.

        DELETE /api/v3/data/{baseId}/{tableId}/links/{linkFieldId}/{recordId}

        Args:
            base_id: The base (project) ID
            table_id: The table ID
            link_field_id: The link field ID
            record_id: The record ID to unlink from
            linked_record_ids: Single ID or list of IDs of records to unlink

        Returns:
            List of unlinked record IDs
            Example: [{"id": 1}, {"id": 2}]
        """
        url = self.__api_info.get_linked_records_uri(base_id, table_id, link_field_id, str(record_id))

        # Normalize to list format for API
        if isinstance(linked_record_ids, (int, str)):
            body = [{"id": linked_record_ids}]
        else:
            body = [{"id": rid} for rid in linked_record_ids]

        return self._request("DELETE", url, json=body).json()

    def attachment_upload_v3(
        self,
        base_id: str,
        table_id: str,
        record_id: Union[int, str],
        field_id: str,
        filename: str,
        content: bytes,
        content_type: str,
    ) -> Dict[str, Any]:
        """Upload attachment to a record field using v3 API.

        POST /api/v3/data/{baseId}/{tableId}/records/{recordId}/fields/{fieldId}/upload

        Args:
            base_id: The base (project) ID
            table_id: The table ID
            record_id: The record ID
            field_id: The attachment field ID
            filename: The filename for the uploaded file
            content: The file content as bytes
            content_type: The MIME type of the file (e.g., "image/png")

        Returns:
            The uploaded attachment metadata
            Example: {"url": "https://...", "title": "image.png", "mimetype": "image/png"}
        """
        url = self.__api_info.get_attachment_upload_uri(
            base_id, table_id, str(record_id), field_id
        )

        # Convert bytes content to base64
        file_base64 = base64.b64encode(content).decode("utf-8")

        body = {
            "contentType": content_type,
            "file": file_base64,
            "filename": filename
        }

        return self._request("POST", url, json=body).json()

    # =========================================================================
    # v3 Meta API Methods
    # =========================================================================

    def workspaces_list_v3(
        self,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """List workspaces using v3 API (Enterprise feature).

        GET /api/v3/meta/workspaces

        Args:
            params: Optional query parameters

        Returns:
            Dict with 'workspaces' array
            Example: {"workspaces": [{"id": "ws_abc", "title": "My Workspace"}]}
        """
        url = self.__api_info.get_workspaces_uri()
        return self._request("GET", url, params=params).json()

    def bases_list_v3(
        self,
        workspace_id: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """List bases using v2 API (v3 is Enterprise-only).

        Note: Despite the method name, this uses v2 API because v3 bases list
        is Enterprise-only and not available in self-hosted NocoDB.

        GET /api/v2/meta/bases

        Args:
            workspace_id: Ignored for self-hosted (no workspaces in community edition)
            params: Optional query parameters

        Returns:
            Dict with 'list' array of bases
            Example: {"list": [{"id": "base_abc", "title": "My Base"}]}
        """
        # Use v2 API - v3 bases list is Enterprise-only
        url = self.__api_info.get_bases_list_uri_v2()
        return self._request("GET", url, params=params).json()

    def bases_list(
        self,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """List all bases using v2 API (for self-hosted NocoDB).

        GET /api/v2/meta/bases

        Note: This uses v2 API because v3 bases list is Enterprise-only.
        Self-hosted NocoDB community edition must use this endpoint.

        Args:
            params: Optional query parameters

        Returns:
            Dict with 'list' array of bases
            Example: {"list": [{"id": "...", "title": "...", ...}]}
        """
        url = self.__api_info.get_bases_list_uri_v2()
        return self._request("GET", url, params=params).json()

    def base_create(
        self,
        body: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a new base using v2 API.

        POST /api/v2/meta/bases

        Note: v3 base creation is Enterprise-only. Self-hosted NocoDB must use v2.

        Args:
            body: Base configuration with 'title' key
                Example: {"title": "My New Base"}

        Returns:
            Created base object with id, title, etc.
            Example: {"id": "base_abc", "title": "My New Base", ...}
        """
        url = self.__api_info.get_base_create_uri_v2()
        return self._request("POST", url, json=body).json()

    def base_read(
        self,
        base_id: str,
    ) -> Dict[str, Any]:
        """Read a single base's metadata using v3 API.

        GET /api/v3/meta/bases/{baseId}

        Args:
            base_id: The base (project) ID

        Returns:
            Base object with id, title, tables, etc.
        """
        url = self.__api_info.get_base_uri(base_id)
        return self._request("GET", url).json()

    def base_update(
        self,
        base_id: str,
        body: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update a base's metadata using v3 API.

        PATCH /api/v3/meta/bases/{baseId}

        Args:
            base_id: The base (project) ID
            body: Fields to update (e.g., {"title": "NewName"})

        Returns:
            Updated base object
        """
        url = self.__api_info.get_base_uri(base_id)
        return self._request("PATCH", url, json=body).json()

    def base_delete(
        self,
        base_id: str,
    ) -> Dict[str, Any]:
        """Delete a base using v3 API.

        DELETE /api/v3/meta/bases/{baseId}

        Args:
            base_id: The base (project) ID

        Returns:
            Deletion confirmation
        """
        url = self.__api_info.get_base_uri(base_id)
        return self._request("DELETE", url).json()

    def tables_list_v3(
        self,
        base_id: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """List tables in a base using v3 API.

        GET /api/v3/meta/bases/{baseId}/tables

        Args:
            base_id: The base (project) ID
            params: Optional query parameters

        Returns:
            Dict with 'list' array
            Example: {"list": [{"id": "tbl_abc", "title": "My Table"}]}
        """
        url = self.__api_info.get_tables_uri(base_id)
        return self._request("GET", url, params=params).json()

    def table_create_v3(
        self,
        base_id: str,
        body: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a new table using v3 API.

        POST /api/v3/meta/bases/{baseId}/tables

        Args:
            base_id: The base (project) ID
            body: Table configuration (title, fields, etc.)
                Example: {"title": "MyTable", "fields": [...]}

        Returns:
            Created table object with id, title, etc.
        """
        url = self.__api_info.get_tables_uri(base_id)
        return self._request("POST", url, json=body).json()

    def table_read_v3(
        self,
        base_id: str,
        table_id: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Read a single table's metadata using v3 API.

        GET /api/v3/meta/bases/{baseId}/tables/{tableId}

        Args:
            base_id: The base (project) ID
            table_id: The table ID
            params: Optional query parameters

        Returns:
            Table object with id, title, columns, etc.
        """
        url = self.__api_info.get_table_meta_uri_v3(base_id, table_id)
        return self._request("GET", url, params=params).json()

    def table_update_v3(
        self,
        base_id: str,
        table_id: str,
        body: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update a table's metadata using v3 API.

        PATCH /api/v3/meta/bases/{baseId}/tables/{tableId}

        Args:
            base_id: The base (project) ID
            table_id: The table ID
            body: Fields to update (e.g., {"title": "NewName"})

        Returns:
            Updated table object
        """
        url = self.__api_info.get_table_meta_uri_v3(base_id, table_id)
        return self._request("PATCH", url, json=body).json()

    def table_delete_v3(
        self,
        base_id: str,
        table_id: str,
    ) -> Dict[str, Any]:
        """Delete a table using v3 API.

        DELETE /api/v3/meta/bases/{baseId}/tables/{tableId}

        Args:
            base_id: The base (project) ID
            table_id: The table ID

        Returns:
            Deletion confirmation
        """
        url = self.__api_info.get_table_meta_uri_v3(base_id, table_id)
        return self._request("DELETE", url).json()

    # =========================================================================
    # v3 Meta API Methods - Fields
    # =========================================================================

    def fields_list_v3(
        self,
        base_id: str,
        table_id: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """List all fields/columns in a table.

        Note: v3 API does not have a separate fields list endpoint.
        This method retrieves fields from the table schema via table_read_v3.

        Args:
            base_id: The base (project) ID
            table_id: The table ID
            params: Optional query parameters passed to table_read_v3

        Returns:
            Dict with 'list' array of fields
            Example: {"list": [{"id": "fld_abc", "title": "Name", "type": "SingleLineText"}]}
        """
        # v3 API includes fields in table read response
        table_info = self.table_read_v3(base_id, table_id, params=params)
        return {"list": table_info.get("fields", [])}

    def field_create_v3(
        self,
        base_id: str,
        table_id: str,
        body: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a new field/column in a table.

        POST /api/v3/meta/bases/{baseId}/tables/{tableId}/fields

        Args:
            base_id: The base (project) ID
            table_id: The table ID
            body: Field configuration (title, type, options)
                Example: {"title": "Email", "type": "Email"}
                For Links: {"title": "Tasks", "type": "Links", "options": {"relation_type": "mm", "related_table_id": "tbl_xyz"}}

        Returns:
            Created field object with id, title, type, etc.
        """
        url = self.__api_info.get_fields_uri(base_id, table_id)
        return self._request("POST", url, json=body).json()

    def field_read_v3(
        self,
        base_id: str,
        field_id: str,
    ) -> Dict[str, Any]:
        """Get details of a specific field/column.

        GET /api/v3/meta/bases/{baseId}/fields/{fieldId}

        Args:
            base_id: The base (project) ID
            field_id: The field ID

        Returns:
            Field object with id, title, type, etc.
            Example: {"id": "fld_abc", "title": "Name", "type": "SingleLineText"}
        """
        url = self.__api_info.get_field_uri(base_id, field_id)
        return self._request("GET", url).json()

    def field_update_v3(
        self,
        base_id: str,
        field_id: str,
        body: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update a field/column.

        PATCH /api/v3/meta/bases/{baseId}/fields/{fieldId}

        Args:
            base_id: The base (project) ID
            field_id: The field ID
            body: Fields to update (e.g., {"title": "NewName"})

        Returns:
            Updated field object
        """
        url = self.__api_info.get_field_uri(base_id, field_id)
        return self._request("PATCH", url, json=body).json()

    def field_delete_v3(
        self,
        base_id: str,
        field_id: str,
    ) -> Dict[str, Any]:
        """Delete a field/column.

        DELETE /api/v3/meta/bases/{baseId}/fields/{fieldId}

        Args:
            base_id: The base (project) ID
            field_id: The field ID

        Returns:
            Deletion confirmation
        """
        url = self.__api_info.get_field_uri(base_id, field_id)
        return self._request("DELETE", url).json()

    def column_update_v2(
        self,
        column_id: str,
        body: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update a column using v2 API.

        PATCH /api/v2/meta/columns/{columnId}

        Note: v3 field update doesn't support colOptions updates (returns 400).
        Use this method for updating SingleSelect/MultiSelect colors.

        Args:
            column_id: The column (field) ID
            body: Fields to update (e.g., {"colOptions": {"options": [...]}})

        Returns:
            Updated column object
        """
        url = self.__api_info.get_column_uri_v2(column_id)
        return self._request("PATCH", url, json=body).json()

    # =========================================================================
    # Backwards Compatibility Aliases (column -> field)
    # =========================================================================

    def columns_list_v3(
        self,
        base_id: str,
        table_id: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Alias for fields_list_v3 (backwards compatibility).

        .. deprecated:: 3.0.0
            Use :meth:`fields_list_v3` instead.
        """
        warnings.warn(
            "columns_list_v3() is deprecated. Use fields_list_v3() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.fields_list_v3(base_id, table_id, params)

    def column_create_v3(
        self,
        base_id: str,
        table_id: str,
        body: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Alias for field_create_v3 (backwards compatibility).

        .. deprecated:: 3.0.0
            Use :meth:`field_create_v3` instead.
        """
        warnings.warn(
            "column_create_v3() is deprecated. Use field_create_v3() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.field_create_v3(base_id, table_id, body)

    def column_read_v3(
        self,
        base_id: str,
        field_id: str,
    ) -> Dict[str, Any]:
        """Alias for field_read_v3 (backwards compatibility).

        .. deprecated:: 3.0.0
            Use :meth:`field_read_v3` instead.
        """
        warnings.warn(
            "column_read_v3() is deprecated. Use field_read_v3() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.field_read_v3(base_id, field_id)

    def column_update_v3(
        self,
        base_id: str,
        field_id: str,
        body: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Alias for field_update_v3 (backwards compatibility).

        .. deprecated:: 3.0.0
            Use :meth:`field_update_v3` instead.
        """
        warnings.warn(
            "column_update_v3() is deprecated. Use field_update_v3() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.field_update_v3(base_id, field_id, body)

    def column_delete_v3(
        self,
        base_id: str,
        field_id: str,
    ) -> Dict[str, Any]:
        """Alias for field_delete_v3 (backwards compatibility).

        .. deprecated:: 3.0.0
            Use :meth:`field_delete_v3` instead.
        """
        warnings.warn(
            "column_delete_v3() is deprecated. Use field_delete_v3() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.field_delete_v3(base_id, field_id)

    # =========================================================================
    # v2 Meta API Methods - Views
    # =========================================================================

    def views_list(
        self,
        table_id: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """List all views for a table using v2 API.

        GET /api/v2/meta/tables/{tableId}/views

        Note: v3 Views API is Enterprise-only. Self-hosted NocoDB must use v2.

        Args:
            table_id: The table ID
            params: Optional query parameters

        Returns:
            Dict with 'list' array of views
            Example: {"list": [{"id": "vw_abc", "title": "Grid View", "type": 3}]}
        """
        url = self.__api_info.get_views_uri(table_id)
        return self._request("GET", url, params=params).json()

    # Note: view_create and view_read are not supported in self-hosted NocoDB v2 API

    def view_update(
        self,
        view_id: str,
        body: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update a view's metadata using v2 API.

        PATCH /api/v2/meta/views/{viewId}

        Note: v3 Views API is Enterprise-only. Self-hosted NocoDB must use v2.

        Args:
            view_id: The view ID
            body: Fields to update (e.g., {"title": "NewName"})

        Returns:
            Updated view object
        """
        url = self.__api_info.get_view_uri(view_id)
        return self._request("PATCH", url, json=body).json()

    def view_delete(
        self,
        view_id: str,
    ) -> Dict[str, Any]:
        """Delete a view using v2 API.

        DELETE /api/v2/meta/views/{viewId}

        Note: v3 Views API is Enterprise-only. Self-hosted NocoDB must use v2.

        Args:
            view_id: The view ID

        Returns:
            Deletion confirmation
        """
        url = self.__api_info.get_view_uri(view_id)
        return self._request("DELETE", url).json()

    # =========================================================================
    # v2 Meta API Methods - View Sorts
    # =========================================================================

    def view_sorts_list(
        self,
        view_id: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """List all sorts for a view using v2 API.

        GET /api/v2/meta/views/{viewId}/sorts

        Note: v3 Views API is Enterprise-only. Self-hosted NocoDB must use v2.

        Args:
            view_id: The view ID
            params: Optional query parameters

        Returns:
            Dict with 'sorts' array
            Example: {"sorts": [{"id": "srt_abc", "fk_column_id": "fld_123", "direction": "asc"}]}
        """
        url = self.__api_info.get_view_sorts_uri(view_id)
        return self._request("GET", url, params=params).json()

    def view_sort_create(
        self,
        view_id: str,
        body: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a new sort for a view using v2 API.

        POST /api/v2/meta/views/{viewId}/sorts

        Note: v3 Views API is Enterprise-only. Self-hosted NocoDB must use v2.

        Args:
            view_id: The view ID
            body: Sort configuration
                Example: {"fk_column_id": "fld_123", "direction": "asc"}

        Returns:
            Created sort object with id, fk_column_id, direction, etc.
        """
        url = self.__api_info.get_view_sorts_uri(view_id)
        return self._request("POST", url, json=body).json()

    def view_sort_update(
        self,
        sort_id: str,
        body: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update a sort using v2 API.

        PATCH /api/v2/meta/sorts/{sortId}

        Note: v3 Views API is Enterprise-only. Self-hosted NocoDB must use v2.

        Args:
            sort_id: The sort ID
            body: Fields to update (e.g., {"direction": "desc"})

        Returns:
            Updated sort object
        """
        url = self.__api_info.get_sort_uri(sort_id)
        return self._request("PATCH", url, json=body).json()

    def view_sort_delete(
        self,
        sort_id: str,
    ) -> Dict[str, Any]:
        """Delete a sort using v2 API.

        DELETE /api/v2/meta/sorts/{sortId}

        Note: v3 Views API is Enterprise-only. Self-hosted NocoDB must use v2.

        Args:
            sort_id: The sort ID

        Returns:
            Deletion confirmation
        """
        url = self.__api_info.get_sort_uri(sort_id)
        return self._request("DELETE", url).json()

    # =========================================================================
    # v2 Meta API Methods - View Filters
    # =========================================================================

    def view_filters_list(
        self,
        view_id: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """List all filters for a view using v2 API.

        GET /api/v2/meta/views/{viewId}/filters

        Note: v3 View Filters API is Enterprise-only. Self-hosted NocoDB must use v2.

        Args:
            view_id: The view ID
            params: Optional query parameters

        Returns:
            Dict with 'list' array of filters
            Example: {"list": [{"id": "flt_abc", "fk_column_id": "fld_123", "comparison_op": "eq", "value": "test"}]}
        """
        url = self.__api_info.get_view_filters_uri(view_id)
        return self._request("GET", url, params=params).json()

    def view_filter_create(
        self,
        view_id: str,
        body: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a new filter for a view using v2 API.

        POST /api/v2/meta/views/{viewId}/filters

        Note: v3 View Filters API is Enterprise-only. Self-hosted NocoDB must use v2.

        Filter comparison operators:
            - eq, neq: Equal, Not equal
            - like, nlike: Like, Not like
            - gt, lt, gte, lte: Greater/Less than (or equal)
            - is, isnot: Is null, Is not null
            - empty, notempty: Is empty, Is not empty
            - in, notin: In array, Not in array

        Args:
            view_id: The view ID
            body: Filter configuration
                Example: {"fk_column_id": "fld_123", "comparison_op": "eq", "value": "test"}

        Returns:
            Created filter object with id, fk_column_id, comparison_op, value, etc.
        """
        url = self.__api_info.get_view_filters_uri(view_id)
        return self._request("POST", url, json=body).json()

    def view_filter_update(
        self,
        filter_id: str,
        body: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update a filter using v2 API.

        PATCH /api/v2/meta/filters/{filterId}

        Note: v3 View Filters API is Enterprise-only. Self-hosted NocoDB must use v2.

        Args:
            filter_id: The filter ID
            body: Fields to update (e.g., {"comparison_op": "neq", "value": "updated"})

        Returns:
            Updated filter object
        """
        url = self.__api_info.get_filter_uri(filter_id)
        return self._request("PATCH", url, json=body).json()

    def view_filter_delete(
        self,
        filter_id: str,
    ) -> Dict[str, Any]:
        """Delete a filter using v2 API.

        DELETE /api/v2/meta/filters/{filterId}

        Note: v3 View Filters API is Enterprise-only. Self-hosted NocoDB must use v2.

        Args:
            filter_id: The filter ID

        Returns:
            Deletion confirmation
        """
        url = self.__api_info.get_filter_uri(filter_id)
        return self._request("DELETE", url).json()

    # =========================================================================
    # v2 Meta API Methods - Webhooks
    # =========================================================================

    def webhooks_list(
        self,
        table_id: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """List all webhooks for a table using v2 API.

        GET /api/v2/meta/tables/{tableId}/hooks

        Note: Webhooks haven't migrated to v3 yet. Use v2 API.

        Args:
            table_id: The table ID
            params: Optional query parameters

        Returns:
            Dict with 'list' array of webhooks
            Example: {"list": [{"id": "hk_abc", "title": "My Webhook", "event": "after.insert"}]}
        """
        url = self.__api_info.get_webhooks_uri(table_id)
        return self._request("GET", url, params=params).json()

    # Note: webhook_create, webhook_read, webhook_update are not supported in self-hosted NocoDB v2 API

    def webhook_delete(
        self,
        hook_id: str,
    ) -> Dict[str, Any]:
        """Delete a webhook using v2 API.

        DELETE /api/v2/meta/hooks/{hookId}

        Note: Webhooks haven't migrated to v3 yet. Use v2 API.

        Args:
            hook_id: The webhook (hook) ID

        Returns:
            Deletion confirmation
        """
        url = self.__api_info.get_webhook_uri(hook_id)
        return self._request("DELETE", url).json()

    # Note: webhook_test is not supported in self-hosted NocoDB v2 API

    # =========================================================================
    # v3 Meta API Methods - Base Members
    # =========================================================================

    def base_members_list(
        self,
        base_id: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """List all members of a base.

        GET /api/v3/meta/bases/{baseId}/members

        Args:
            base_id: The base (project) ID
            params: Optional query parameters

        Returns:
            Dict with 'members' array
            Example: {"members": [{"id": "usr_abc", "email": "user@example.com", "roles": "editor"}]}
        """
        url = self.__api_info.get_base_members_uri(base_id)
        return self._request("GET", url, params=params).json()

    def base_member_add(
        self,
        base_id: str,
        body: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Add a member to a base.

        POST /api/v3/meta/bases/{baseId}/members

        Args:
            base_id: The base (project) ID
            body: Member configuration with email and roles
                Example: {"email": "user@example.com", "roles": "editor"}
                Roles: owner, creator, editor, commenter, viewer

        Returns:
            Created member object
        """
        url = self.__api_info.get_base_members_uri(base_id)
        return self._request("POST", url, json=body).json()

    def base_member_update(
        self,
        base_id: str,
        member_id: str,
        body: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update a base member's role.

        PATCH /api/v3/meta/bases/{baseId}/members/{memberId}

        Args:
            base_id: The base (project) ID
            member_id: The member ID
            body: Fields to update (e.g., {"roles": "viewer"})
                Roles: owner, creator, editor, commenter, viewer

        Returns:
            Updated member object
        """
        url = self.__api_info.get_base_member_uri(base_id, member_id)
        return self._request("PATCH", url, json=body).json()

    def base_member_remove(
        self,
        base_id: str,
        member_id: str,
    ) -> Dict[str, Any]:
        """Remove a member from a base.

        DELETE /api/v3/meta/bases/{baseId}/members/{memberId}

        Args:
            base_id: The base (project) ID
            member_id: The member ID

        Returns:
            Deletion confirmation
        """
        url = self.__api_info.get_base_member_uri(base_id, member_id)
        return self._request("DELETE", url).json()

    # =========================================================================
    # v2 Export API Methods
    # =========================================================================

    def export_view(
        self,
        base_id: str,
        view_id: str,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        poll_interval: float = 1.0,
        timeout: float = 300.0,
    ) -> bytes:
        """Export view data as CSV.

        POST /api/v2/export/{viewId}/csv

        This endpoint triggers an async export job. The method polls for completion
        and returns the CSV content when ready.

        Note: Only CSV format is supported in self-hosted NocoDB.

        Args:
            base_id: The base ID (required for job status polling)
            view_id: The view ID
            offset: Optional row offset for pagination
            limit: Optional row limit
            poll_interval: Seconds between status checks (default: 1.0)
            timeout: Maximum seconds to wait for export (default: 300.0)

        Returns:
            CSV file content as bytes

        Raises:
            NocoDBAPIError: If export fails or times out
        """
        import time

        url = self.__api_info.get_export_uri(view_id)
        params = {}
        if offset is not None:
            params["offset"] = offset
        if limit is not None:
            params["limit"] = limit

        response = self._request("POST", url, params=params if params else None)

        # Check response content type to determine if it's direct CSV or job result
        content_type = response.headers.get("Content-Type", "")

        # If direct CSV content returned (synchronous response)
        if "text/csv" in content_type or "application/octet-stream" in content_type:
            return response.content

        # If JSON job response, poll for completion
        if "application/json" in content_type:
            job_data = response.json()

            # If direct download URL provided
            if "url" in job_data:
                download_response = self.__session.get(job_data["url"])
                download_response.raise_for_status()
                return download_response.content

            # If job ID provided, poll for completion
            job_id = job_data.get("id") or job_data.get("job_id")
            if job_id:
                start_time = time.time()
                jobs_url = self.__api_info.get_jobs_uri(base_id)
                while time.time() - start_time < timeout:
                    # Check job status via POST /api/v2/jobs/{baseId}
                    # Query all jobs with empty body, then find ours
                    status_response = self._request("POST", jobs_url, json={})
                    status_data = status_response.json()

                    # Response contains list of jobs, find ours
                    jobs = status_data if isinstance(status_data, list) else [status_data]
                    for job in jobs:
                        if job.get("id") == job_id:
                            status = job.get("status", "").lower()
                            if status in ("completed", "done", "success"):
                                # Get download URL from result
                                result = job.get("result", {})
                                download_path = result.get("url") if isinstance(result, dict) else None
                                if download_path:
                                    # Build full URL from relative path
                                    download_url = self.__api_info.get_download_uri(download_path)
                                    download_response = self.__session.get(download_url)
                                    download_response.raise_for_status()
                                    return download_response.content
                                # If result is inline
                                if "data" in job:
                                    return job["data"].encode("utf-8")

                            if status in ("failed", "error"):
                                raise NocoDBAPIError(
                                    f"Export job failed: {job.get('error', 'Unknown error')}"
                                )
                            break

                    time.sleep(poll_interval)

                raise NocoDBAPIError(f"Export timed out after {timeout} seconds")

        # Fallback: return raw content
        return response.content

    # =========================================================================
    # v2 View Columns API Methods
    # =========================================================================

    def view_columns_list(
        self,
        view_id: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """List all columns in a view with visibility settings.

        GET /api/v2/meta/views/{viewId}/columns

        Args:
            view_id: The view ID
            params: Optional query parameters

        Returns:
            Dict with column visibility information
            Example: {"list": [{"id": "col_abc", "fk_column_id": "fld_123", "show": true, "order": 1}]}
        """
        url = self.__api_info.get_view_columns_uri(view_id)
        return self._request("GET", url, params=params).json()

    def view_column_create(
        self,
        view_id: str,
        body: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a view column visibility setting.

        POST /api/v2/meta/views/{viewId}/columns

        Args:
            view_id: The view ID
            body: Column configuration
                Example: {"fk_column_id": "fld_123", "show": true, "order": 1}

        Returns:
            Created view column object
        """
        url = self.__api_info.get_view_columns_uri(view_id)
        return self._request("POST", url, json=body).json()

    def view_column_update(
        self,
        view_id: str,
        column_id: str,
        body: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update a view column's visibility or order.

        PATCH /api/v2/meta/views/{viewId}/columns/{columnId}

        Args:
            view_id: The view ID
            column_id: The view column ID
            body: Fields to update (e.g., {"show": false, "order": 5})

        Returns:
            Updated view column object
        """
        url = self.__api_info.get_view_column_uri(view_id, column_id)
        return self._request("PATCH", url, json=body).json()

    def view_columns_hide_all(
        self,
        view_id: str,
    ) -> Dict[str, Any]:
        """Hide all columns in a view.

        POST /api/v2/meta/views/{viewId}/hide-all

        Args:
            view_id: The view ID

        Returns:
            Operation confirmation
        """
        url = self.__api_info.get_view_hide_all_uri(view_id)
        return self._request("POST", url).json()

    def view_columns_show_all(
        self,
        view_id: str,
    ) -> Dict[str, Any]:
        """Show all columns in a view.

        POST /api/v2/meta/views/{viewId}/show-all

        Args:
            view_id: The view ID

        Returns:
            Operation confirmation
        """
        url = self.__api_info.get_view_show_all_uri(view_id)
        return self._request("POST", url).json()

    # =========================================================================
    # v2 Shared Views API Methods
    # =========================================================================

    def shared_views_list(
        self,
        table_id: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """List all shared views for a table.

        GET /api/v2/meta/tables/{tableId}/share

        Args:
            table_id: The table ID
            params: Optional query parameters

        Returns:
            Dict with shared views list
            Example: {"list": [{"id": "sv_abc", "fk_view_id": "vw_123", "uuid": "..."}]}
        """
        url = self.__api_info.get_shared_views_uri(table_id)
        return self._request("GET", url, params=params).json()

    def shared_view_create(
        self,
        view_id: str,
        password: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a shared (public) view link.

        POST /api/v2/meta/views/{viewId}/share

        Args:
            view_id: The view ID
            password: Optional password protection for the share

        Returns:
            Created shared view object with uuid for public URL
            Example: {"uuid": "abc123...", "url": "..."}
        """
        url = self.__api_info.get_shared_view_uri(view_id)
        body = {}
        if password:
            body["password"] = password
        return self._request("POST", url, json=body if body else None).json()

    def shared_view_update(
        self,
        view_id: str,
        password: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update a shared view's settings.

        PATCH /api/v2/meta/views/{viewId}/share

        Args:
            view_id: The view ID
            password: New password (or None to remove password)

        Returns:
            Updated shared view object
        """
        url = self.__api_info.get_shared_view_uri(view_id)
        body = {"password": password}
        return self._request("PATCH", url, json=body).json()

    def shared_view_delete(
        self,
        view_id: str,
    ) -> Dict[str, Any]:
        """Delete a shared view link.

        DELETE /api/v2/meta/views/{viewId}/share

        Args:
            view_id: The view ID

        Returns:
            Deletion confirmation
        """
        url = self.__api_info.get_shared_view_uri(view_id)
        return self._request("DELETE", url).json()

    # =========================================================================
    # v2 Storage API Methods
    # =========================================================================

    def storage_upload(
        self,
        filename: str,
        content: bytes,
        content_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Upload a file to NocoDB storage.

        POST /api/v2/storage/upload

        Note: This is for general file upload, not record-attached attachments.
        Use attachment_upload_v3 for attaching files to records.

        Args:
            filename: The filename for the uploaded file
            content: The file content as bytes
            content_type: Optional MIME type (auto-detected if not provided)

        Returns:
            Uploaded file metadata with URL
            Example: {"url": "https://...", "title": "file.pdf", "mimetype": "application/pdf"}
        """
        import mimetypes as mt

        url = self.__api_info.get_storage_upload_uri()

        if content_type is None:
            detected_type, _ = mt.guess_type(filename)
            content_type = detected_type or "application/octet-stream"

        # Use multipart form upload
        files = {
            "file": (filename, content, content_type)
        }

        # Use requests.post directly instead of session to avoid
        # Content-Type: application/json header interfering with multipart boundary
        # Only include auth header, let requests auto-generate multipart Content-Type
        auth_headers = {
            k: v for k, v in self.__session.headers.items()
            if k.lower() != "content-type"
        }

        response = requests.post(url, files=files, headers=auth_headers)
        response.raise_for_status()
        return response.json()

    # =========================================================================
    # v2 Filter/Sort Metadata API Methods
    # =========================================================================

    def view_filter_get(
        self,
        filter_id: str,
    ) -> Dict[str, Any]:
        """Get a single filter's details.

        GET /api/v2/meta/filters/{filterId}

        Args:
            filter_id: The filter ID

        Returns:
            Filter object with id, fk_column_id, comparison_op, value, etc.
        """
        url = self.__api_info.get_filter_uri(filter_id)
        return self._request("GET", url).json()

    def view_sort_get(
        self,
        sort_id: str,
    ) -> Dict[str, Any]:
        """Get a single sort's details.

        GET /api/v2/meta/sorts/{sortId}

        Args:
            sort_id: The sort ID

        Returns:
            Sort object with id, fk_column_id, direction, etc.
        """
        url = self.__api_info.get_sort_uri(sort_id)
        return self._request("GET", url).json()

    def view_filter_children(
        self,
        filter_group_id: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """List children of a filter group.

        GET /api/v2/meta/filters/{filterGroupId}/children

        Args:
            filter_group_id: The filter group ID
            params: Optional query parameters

        Returns:
            Dict with nested filters list
        """
        url = self.__api_info.get_filter_children_uri(filter_group_id)
        return self._request("GET", url, params=params).json()

    # =========================================================================
    # v2 Webhook Filters/Logs API Methods
    # =========================================================================

    def webhook_filters_list(
        self,
        hook_id: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """List all filters for a webhook.

        GET /api/v2/meta/hooks/{hookId}/filters

        Args:
            hook_id: The webhook (hook) ID
            params: Optional query parameters

        Returns:
            Dict with webhook filters list
        """
        url = self.__api_info.get_webhook_filters_uri(hook_id)
        return self._request("GET", url, params=params).json()

    def webhook_filter_create(
        self,
        hook_id: str,
        body: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a filter for a webhook.

        POST /api/v2/meta/hooks/{hookId}/filters

        Args:
            hook_id: The webhook (hook) ID
            body: Filter configuration
                Example: {"fk_column_id": "fld_123", "comparison_op": "eq", "value": "test"}

        Returns:
            Created webhook filter object
        """
        url = self.__api_info.get_webhook_filters_uri(hook_id)
        return self._request("POST", url, json=body).json()

    def webhook_logs(
        self,
        hook_id: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """List execution logs for a webhook.

        GET /api/v2/meta/hooks/{hookId}/logs

        Args:
            hook_id: The webhook (hook) ID
            params: Optional query parameters

        Returns:
            Dict with webhook execution logs
        """
        url = self.__api_info.get_webhook_logs_uri(hook_id)
        return self._request("GET", url, params=params).json()

    def webhook_sample_payload(
        self,
        table_id: str,
        event: str,
        operation: str,
        version: str = "v2",
    ) -> Dict[str, Any]:
        """Get a sample webhook payload for preview.

        GET /api/v2/meta/tables/{tableId}/hooks/samplePayload/{event}/{operation}/{version}

        Args:
            table_id: The table ID
            event: The event type (e.g., "records")
            operation: The operation (e.g., "insert", "update", "delete")
            version: The payload version (default: "v2")

        Returns:
            Sample webhook payload structure
        """
        url = self.__api_info.get_webhook_sample_payload_uri(table_id, event, operation, version)
        return self._request("GET", url).json()
