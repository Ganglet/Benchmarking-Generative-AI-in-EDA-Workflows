`timescale 1ns / 1ps

module pipo_register_8bit (
    input  wire        clk,
    input  wire        rst,
    input  wire        en,
    input  wire [7:0]  d,
    output reg  [7:0]  q
);
    always @(posedge clk) begin
        if (rst) begin
            q <= 8'h00;
        end else if (en) begin
            q <= d;
        end
    end
endmodule

