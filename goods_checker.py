import argparse
import pandas
import math
import sys
import os


class CheckCategories:
    """Основной класс скрипта"""
    def __init__(self):
        self.args_parser = argparse.ArgumentParser()
        self.args_parser.add_argument("--csv1")
        self.args_parser.add_argument("--csv2")
        self.args_parser.add_argument("--view", default="csv")
        self.args_parser.add_argument("--cat", default="")
        self.args_parser.add_argument("--path", default="", required=False)
        self.args_parser.add_argument("--all-sku", default=False, action="store_true")
        self.args_parser.add_argument("--output-file", default="")
        self.args = self.args_parser.parse_args()
        self.work_dir: str = ""
        self.csvs_info: dict = {}
        self.output_data: dict = {}

    def start(self) -> None:
        """Запуск скрипта"""
        print(f"Начинаем работу. Режим проверки наличия товаров в категории {self.args.cat}" if self.args.cat else
              "Начинаем работу. Режим подсчета количества товаров в категориях")
        self.csvs_info["csv1"] = {
            "path": self.make_file_path(self.args.csv1),
            "name": self.args.csv1.split("/")[-1] if "/" in self.args.csv1 else self.args.csv1.split("\"")[-1],
            "date": self.args.csv1.split("_")[-2]
        }
        self.csvs_info["csv2"] = {
            "path": self.make_file_path(self.args.csv2),
            "name": self.args.csv2.split("/")[-1] if "/" in self.args.csv2 else self.args.csv2.split("\"")[-1],
            "date": self.args.csv2.split("_")[-2]
        }

        if self.csvs_info["csv1"]["date"] == self.csvs_info["csv2"]["date"]:
            self.csvs_info["csv1"]["date"] = f"csv1 {self.csvs_info['csv1']['date']}"
            self.csvs_info["csv2"]["date"] = f"csv2 {self.csvs_info['csv2']['date']}"

        for csv_key, params in self.csvs_info.items():
            print(f"{csv_key}:", params["name"])
            if not params["name"].endswith(".csv"):
                self.stop_script(f"Неверно выбран файл! Заданный файл {csv_key} имеет расширение не .csv")

            if self.args.cat:
                self.work_with_file(csv_key, "sku_name")
            else:
                self.work_with_file(csv_key, "sku_category")

        if not self.output_data:
            self.stop_script("Файлы проверены, но нужных данных не обнаружено! "
                             "Проверьте корректность передаваемых параметров! ")

        if not self.args.cat:
            self.get_goods_difference()

        output_df = pandas.DataFrame.from_dict(self.output_data, orient='index')
        csv1_date = self.csvs_info["csv1"]["date"]
        csv2_date = self.csvs_info["csv2"]["date"]

        if self.args.cat:
            output_df = output_df.sort_values([csv1_date, csv2_date], ascending=[False, False])
            output_df.index.name = "sku_name"
            columns = ["sku_article", csv1_date, csv2_date]
            header = ["sku_article", csv1_date, csv2_date]
        else:
            output_df.index.name = "sku_category"
            columns = [csv1_date, csv2_date, "difference_percent", "difference_amount"]
            header = [csv1_date, csv2_date, "Разница, %", "Разница, SKU"]

        if self.args.view == "console":
            print(output_df.to_string(columns=columns, header=header))
        elif self.args.view == "csv" and not self.args.output_file:
            output_df.to_csv(self.work_dir + "/output.csv", sep=";", encoding="utf-8", header=header, columns=columns)
            print("Данные записаны в файл output.csv")
        elif self.args.view == "csv" and self.args.output_file:
            output_df.to_csv(self.args.output_file, sep=";", encoding="utf-8", header=header, columns=columns)
            print(f"Данные записаны в файл {self.args.output_file}")

    def work_with_file(self, csv_key: str, column_name: str) -> None:
        """
        Работаем с файлом csv, собираем нужные данные

        :param csv_key: ключ файла в self.csvs_info
        :param column_name: имя основной колонки
        :return: None
        """
        csv_dataframe = pandas.read_csv(self.csvs_info[csv_key]["path"], delimiter=";")
        collected_articles: list = []
        for i, row in csv_dataframe.iterrows():
            if (not self.args.cat or row["sku_category"] == self.args.cat) and row["sku_article"] \
                    not in collected_articles:
                collected_articles.append(row["sku_article"])
                if self.args.all_sku:
                    self.collect_good(csv_key, row, column_name)
                elif self.value_is_not_nan(row["sku_status"]) and int(row["sku_status"]) == 1:
                    self.collect_good(csv_key, row, column_name)
                elif not self.value_is_not_nan(row["sku_status"]):
                    self.collect_good(csv_key, row, column_name)

    def collect_good(self, csv_key: str, row: pandas.Series, column_name: str) -> None:
        """
        Записывает данные товара в словарь self.output_data
        """
        if row[column_name] not in self.output_data:
            self.output_data[row[column_name]] = {
                "sku_article": row["sku_article"] if self.args.cat else "",
                self.csvs_info["csv1"]["date"]: 0,
                self.csvs_info["csv2"]["date"]: 0
            }

        self.output_data[row[column_name]][self.csvs_info[csv_key]["date"]] += 1

    def get_goods_difference(self) -> None:
        """
        Вычисляет разницу между количеством товаров в категориях разных csv

        :return: None
        """
        csv1_date = self.csvs_info["csv1"]["date"]
        csv2_date = self.csvs_info["csv2"]["date"]
        for value in self.output_data.values():
            if value[csv1_date] > value[csv2_date]:
                value["difference_percent"] = self.check_for_delimiter(
                    ((value[csv2_date] - value[csv1_date]) / value[csv1_date]) * 100)
                value["difference_percent"] = str(value["difference_percent"]).replace(".", ",")
            elif value[csv1_date] < value[csv2_date]:
                value["difference_percent"] = self.check_for_delimiter(
                    ((value[csv1_date] - value[csv2_date]) / value[csv2_date]) * 100)
                value["difference_percent"] = str(value["difference_percent"]).replace(".", ",").replace("-", "")
            else:
                value["difference_percent"] = 0

            value["difference_amount"] = value[csv2_date] - value[csv1_date]

    def make_file_path(self, file_arg: str) -> str:
        if "/" in file_arg or "\\" in file_arg:
            return file_arg
        else:
            self.work_dir = self.args.path if self.args.path else os.getcwd()
            if os.path.exists(f"{self.work_dir}/{file_arg}"):
                return f"{self.work_dir}/{file_arg}"
            elif os.path.exists(f"{self.work_dir}/out/{file_arg}"):
                return f"{self.work_dir}/out/{file_arg}"
            elif os.path.exists(f"{os.path.realpath(__file__)}{file_arg}".replace("goods_checker.py", "")):
                return f"{os.path.realpath(__file__)}{file_arg}".replace("goods_checker.py", "")
            else:
                self.stop_script(f"Отсутствует файл {file_arg}")

    @staticmethod
    def stop_script(message: str = "") -> None:
        """
        Остановка выполнения скрипта

        :param message: сообщение остановки
        :return: None
        """
        print("Скрипт остановлен. {}".format(f"\nСообщение: {message}" if message else ""))
        sys.exit()

    @staticmethod
    def check_for_delimiter(value):
        try:
            value = float(value)
            if abs(value - int(value)) < 1e-3:
                return int(value)
            else:
                value = round(value, 2)
                if (value * 100) % 10 == 0:
                    return round(value, 1)
                else:
                    return value
        except:
            return ""

    @staticmethod
    def value_is_not_nan(value) -> bool:
        """
        Проверяет не является ли значение NaN.

        :param value: проверяемые данные
        :return: True/False
        """
        if (type(value) == int or type(value) == float) and math.isnan(value):
            return False
        else:
            return True


if __name__ == "__main__":
    script = CheckCategories()
    script.start()
