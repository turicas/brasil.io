# pip install splinter Pillow
import os
import time
from urllib.parse import urljoin

from splinter import Browser


class Covid19Screenshot:
    def __init__(self, base_url="https://brasil.io/", browser="chrome"):
        self.browser = Browser(browser)
        self.base_url = base_url
        self.browser.driver.set_window_size(1400, 10000)

    def css_by_xpath(self, xpath):
        elem = self.browser.find_by_xpath(xpath).first
        css = [x.split(":") for x in elem._element.get_attribute("style").split(";") if x.strip()]
        return {key.strip(): value.strip() for (key, value) in css}

    def visit_dashboard(self, state=None):
        path = "covid19/"
        if state is not None:
            path += f"{state}/"
        self.browser.visit(urljoin(self.base_url, path))

        finished = False
        while not finished:
            css = self.css_by_xpath("//*[@id = 'loading']")
            finished = css.get("z-index", None) == "-999"
            if not finished:
                time.sleep(0.1)

    def _remove_element_from_xpath(self, xpath):
        elem = self.browser.find_by_xpath(xpath).first
        self.browser.execute_script(
            """
            var elem = arguments[0];
            elem.parentNode.removeChild(elem);
            """,
            elem._element,
        )

    def remove_elements(self, for_state=False):
        xpaths = [
            "//div[@id = 'dashboard-state-selector']",
            "//div[@id = 'dashboard-header']",
            "//div[@id = 'table-col']",
        ]
        if for_state:
            xpaths.append("//div[@id = 'dashboard-country-aggregate']")
        for xpath in xpaths:
            self._remove_element_from_xpath(xpath)

        # elem = self.browser.find_by_xpath("//div[@id = 'map-col']").first
        # self.browser.execute_script(
        #    """
        #    var elem = arguments[0];
        #    elem.className = "";
        #    """,
        #    elem._element,
        # )

    def load_dashboard(self, state=None):
        self.visit_dashboard(state=state)
        self.remove_elements(for_state=bool(state))
        time.sleep(1)

    def screenshot(self, filename, state=None):
        temp_filename = self.browser.find_by_xpath("//div[@class = 'container']").screenshot()
        os.rename(temp_filename, filename)

    def close(self):
        self.browser.quit()


if __name__ == "__main__":
    from tqdm import tqdm

    s = Covid19Screenshot()
    states = [None] + "AC AL AM AP BA CE DF ES GO MA MG MS MT PA PB PE PI PR RJ RN RO RR RS SC SE SP TO".split()
    for state in tqdm(states):
        s.load_dashboard(state)
        s.screenshot(f"/tmp/covid19-{state or 'BR'}.png")
    s.close()
