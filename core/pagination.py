import base64
from datetime import datetime, timezone
from typing import Optional, Tuple


class TokenCursorCodec:
    """Handles the transformation of database pagination markers (timestamps and IDs)

    into opaque, URL-safe Base64 string tokens, and vice versa.
    """

    @staticmethod
    def encode(timestamp: datetime, record_id: int) -> str:
        """Takes an item's creation timestamp and unique ID, and bundles them

        into a single URL-safe Base64 token for the frontend client.
        """
        # 1. Convert the datetime to a standard string representation (ISO 8601 format)
        # Example: 2026-07-10T12:00:00+00:00
        iso_timestamp = timestamp.isoformat()

        # 2. Join the timestamp and the record ID using a distinct delimiter
        # Example: "2026-07-10T12:00:00+00:00||42"
        raw_combined_str = f"{iso_timestamp}||{record_id}"

        # 3. Convert the string to bytes, encode it to URL-safe Base64,
        # and decode the bytes back into a clean string to send over the API.
        encoded_bytes = base64.urlsafe_b64encode(raw_combined_str.encode("utf-8"))
        return encoded_bytes.decode("utf-8")

    @staticmethod
    def decode(cursor_string: Optional[str]) -> Optional[Tuple[datetime, int]]:
        """Takes an opaque Base64 token from a client request, decodes it,

        and extracts the exact Python datetime object and integer ID bounds.
        """
        # If the client didn't supply a cursor, they want page 1. Return None.
        if not cursor_string:
            return None

        try:
            # 1. Decode the URL-safe Base64 string back into raw bytes, then to string
            decoded_bytes = base64.urlsafe_b64decode(cursor_string.encode("utf-8"))
            raw_combined_str = decoded_bytes.decode("utf-8")

            # 2. Split the string back into its original timestamp and identity segments
            timestamp_segment, identity_segment = raw_combined_str.split("||")

            # 3. Parse the timestamp text back into an actual Python datetime object
            parsed_timestamp = datetime.fromisoformat(timestamp_segment)

            # 4. Guarantee that the timestamp remains timezone-aware (UTC)
            if parsed_timestamp.tzinfo is None:
                parsed_timestamp = parsed_timestamp.replace(tzinfo=timezone.utc)

            # Return the values as a tuple: (boundary_time, boundary_id)
            return parsed_timestamp, int(identity_segment)

        except Exception:
            # Defensive programming: If a user tampers with the cursor string in the URL,
            # or if decoding fails, don't crash the server. Fall back to returning None
            # which safely drops the user back to the first page of results.
            return None