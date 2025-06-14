from web_interface import _get_html, update_results

def test_update_results_and_html():
    update_results('test data')
    html = _get_html()
    assert 'IfcLCA Results' in html
    assert 'Loading' in html
