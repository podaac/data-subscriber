from subscriber import podaac_access as pa

def test_cmr_search_After():
    params = {
        'page_size': 2000,
        'sort_key': "-start_date",
        'provider': "POCLOUD",
        'ShortName': "ECCO_L4_ATM_STATE_05DEG_DAILY_V4R4"
    }
    print("Testing Search...")
    results = pa.get_search_results(True, params)
    assert len(results) == 9497
