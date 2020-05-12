from covid19.stats import group_deaths


def test_group_deaths():
    data = [
        {
            "epidemiological_week": 10,
            "deaths_covid19": 100,
            "deaths_indeterminate": 200,
            "deaths_indeterminate_2019": 300,
            "deaths_others": 400,
            "deaths_others_2019": 500,
            "deaths_pneumonia": 600,
            "deaths_pneumonia_2019": 700,
            "deaths_respiratory_failure": 800,
            "deaths_respiratory_failure_2019": 900,
            "deaths_sars": 1000,
            "deaths_sars_2019": 1100,
            "deaths_septicemia": 1200,
            "deaths_septicemia_2019": 1300,
            "deaths_total": 1400,
            "deaths_total_2019": 1500,
            "new_deaths_covid19": 1,
            "new_deaths_indeterminate": 2,
            "new_deaths_indeterminate_2019": 3,
            "new_deaths_others": 5,
            "new_deaths_others_2019": 7,
            "new_deaths_pneumonia": 11,
            "new_deaths_pneumonia_2019": 13,
            "new_deaths_respiratory_failure": 19,
            "new_deaths_respiratory_failure_2019": 23,
            "new_deaths_sars": 29,
            "new_deaths_sars_2019": 31,
            "new_deaths_septicemia": 43,
            "new_deaths_septicemia_2019": 53,
            "new_deaths_total": 97,
            "new_deaths_total_2019": 100,
        },
    ]

    result = group_deaths(data)
    assert len(result) == 1

    row = result[0]
    expected_row = {
        "epidemiological_week": 10,
        "deathgroup_other_2019": 300 + 500 + 1300,
        "new_deathgroup_other_2019": 3 + 7 + 53,
        "deathgroup_other_respiratory_2019": 700 + 900 + 1100,
        "new_deathgroup_other_respiratory_2019": 13 + 23 + 31,
        "deathgroup_covid19_2019": 0,
        "new_deathgroup_covid19_2019": 0,
        "deathgroup_other_2020": 200 + 400 + 1200,
        "new_deathgroup_other_2020": 2 + 5 + 43,
        "deathgroup_other_respiratory_2020": 600 + 800 + 1000,
        "new_deathgroup_other_respiratory_2020": 11 + 19 + 29,
        "deathgroup_covid19_2020": 100,
        "new_deathgroup_covid19_2020": 1,
        "excess_deaths": -100,
        "new_excess_deaths": -3,
    }
    assert row == expected_row
