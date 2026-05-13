/** @odoo-module **/

import { loadJS } from "@web/core/assets";
import { useService } from "@web/core/utils/hooks";
import {
  Component,
  useState,
  onWillStart,
  useSubEnv,
  useRef,
  onMounted,
} from "@odoo/owl";

export class PieChart extends Component {
  setup() {
    this.state = useState({ employee_per_location: [] });
    this.chartRef = useRef("pie_chart");
    this.orm = useService("orm");


    onWillStart(async () => {
      await loadJS("/web/static/lib/Chart/Chart.js");

      this.state.employee_per_location = await this.get_employees_per_location();
    });

    onMounted(() => {
      this.renderChart();
    });
  }

  async get_employees_per_location() {
    const result = await this.orm.call(
      "sa.attendance.dashboard",
      "absent_employee_per_location",
      [[]]
    );

    return result;
  }

  renderChart() {
    const data = this.state.employee_per_location

    new Chart(this.chartRef.el, {
      type: "pie",
      data: {
        labels: data.map((row) => row.department_id[1] ? row.department_id[1] : "Not Set"),
        datasets: [
          {
            label: "Employees",
            data: data.map((row) => row.department_id_count),
          },
        ],
      },

     
    });
  }
}

PieChart.template = "softatt_attendance.PieChart"; // Template name
