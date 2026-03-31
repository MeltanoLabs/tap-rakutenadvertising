"""Unit tests for custom paginator classes."""

from unittest.mock import MagicMock

import pytest
import xmltodict

from tap_rakutenadvertising.client import (
    EventsPaginator,
    LinkLocatorPaginator,
    RakutenPaginator,
    XMLPagePaginator,
)


def _json_response(data: object) -> MagicMock:
    response = MagicMock()
    response.json.return_value = data
    return response


def _xml_response(data_dict: dict) -> MagicMock:
    response = MagicMock()
    response.text = xmltodict.unparse(data_dict)
    return response


class TestRakutenPaginator:
    def test_has_more(self):
        """Test has_more() with various response structures."""
        response = _json_response({"_metadata": {"_links": {"next": "/v2/advertisers?page=2"}}})
        paginator = RakutenPaginator()
        url = paginator.get_next(response)
        assert url is not None
        assert url.path == "/v2/advertisers"
        assert url.query == "page=2"

    @pytest.mark.parametrize(
        ("response_data"),
        [
            pytest.param({"_metadata": {"_links": {}}}, id="next_link_absent"),
            pytest.param({"data": []}, id="metadata_missing"),
            pytest.param({"_metadata": {}}, id="links_missing"),
        ],
    )
    def test_no_more(self, response_data: dict):
        """Test has_more() with various response structures."""
        response = _json_response(response_data)
        paginator = RakutenPaginator()
        assert paginator.get_next_url(response) is None


class TestEventsPaginator:
    @pytest.mark.parametrize(
        ("item_count", "page_size", "has_more"),
        [
            pytest.param(100, 100, True, id="full_page"),
            pytest.param(50, 100, False, id="partial_page"),
            pytest.param(0, 100, False, id="empty_page"),
        ],
    )
    def test_has_more(self, item_count: int, page_size: int, has_more: bool):
        response = _json_response([{"id": i} for i in range(item_count)])
        paginator = EventsPaginator(page_size=page_size)
        assert paginator.has_more(response) is has_more



class TestXMLPagePaginator:
    def _make_response(
        self,
        total_pages: int,
        current_page: int,
        page_key: str = "PageNumber",
    ) -> MagicMock:
        return _xml_response(
            {
                "root": {
                    "TotalPages": str(total_pages),
                    page_key: str(current_page),
                },
            }
        )

    @pytest.mark.parametrize(
        ("total_pages", "current_page", "has_more"),
        [
            pytest.param(5, 2, True, id="middle_page"),
            pytest.param(5, 5, False, id="last_page"),
            pytest.param(1, 1, False, id="single_page"),
        ],
    )
    @pytest.mark.parametrize(
        ("page_key"),
        [
            pytest.param(None, id="default_page_key"),
            pytest.param("PageNumberRequested", id="custom_page_key"),
        ],
    )
    def test_has_more_when_on_last_page(
        self,
        page_key: str | None,
        total_pages: int,
        current_page: int,
        has_more: bool,
    ):
        response = self._make_response(
            total_pages=total_pages,
            current_page=current_page,
            page_key=page_key or "PageNumber",
        )
        kwargs = {"current_page_key": page_key} if page_key else {}
        paginator = XMLPagePaginator(**kwargs)
        assert paginator.has_more(response) is has_more

    def test_defaults_to_single_page_when_no_total(self):
        response = _xml_response({"root": {"PageNumber": "1"}})
        paginator = XMLPagePaginator()
        assert paginator.has_more(response) is False


class TestLinkLocatorPaginator:
    _response_key = "ns1:getTextLinksResponse"

    def _make_response(self, items: list[dict] | dict) -> MagicMock:
        return _xml_response({"root": {self._response_key: items}})

    @pytest.mark.parametrize(
        ("items", "has_more"),
        [
            pytest.param([{"ns1:return": {"linkID": "1"}}], True, id="single_item_with_return"),
            pytest.param([{"other_key": "value"}], False, id="single_item_without_return"),
            pytest.param([], False, id="no_items"),
            pytest.param(
                [{"other_key": "value"}, {"ns1:return": {"linkID": "2"}}],
                True,
                id="multiple_items_one_has_return",
            ),
            pytest.param(
                {"ns1:return": {"linkID": "1"}},
                True,
                id="single_dict_item_coerced_to_list",
            ),
        ],
    )
    def test_has_more(self, items: list[dict] | dict, has_more: bool):
        response = self._make_response(items)
        paginator = LinkLocatorPaginator(response_key=self._response_key)
        assert paginator.has_more(response) is has_more
