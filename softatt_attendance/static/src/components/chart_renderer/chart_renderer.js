/** @odoo-module **/

import { loadJS } from "@web/core/assets";

import {
  Component,
  useState,
  onWillStart,
  useSubEnv,
  useRef,
  onMounted,
} from "@odoo/owl";

export class ChartRenderer extends Component {

  


  setup() {
    this.chartRef = useRef("chart");

    onWillStart(async () => {
      await loadJS("/web/static/lib/Chart/Chart.js");
    });

    onMounted(() => {
      this.renderChart();
    });
  }

  renderChart() {
    const data = [
      {
        label: "Present",
        count: 12,
      },
      { label: "absent", count: 5 },
    ];

    new Chart(this.chartRef.el, {
      type: this.props.type,
      data: {
        labels: data.map((row) => row.label),
        datasets: [
          {
            label: "Acquisitions by year",
            data: data.map((row) => row.count),
          },
        ],
      },

      title: {
        display: true,
        text: "Chart.js Pie Chart",
      },
    });
  }
}

ChartRenderer.template = "softatt_attendance.chart_renderer"; // Template name
