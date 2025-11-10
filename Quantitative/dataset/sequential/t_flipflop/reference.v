`timescale 1ns / 1ps

module t_flipflop (
    input  wire clk,
    input  wire rst,
    input  wire t,
    output reg  q
);
    always @(posedge clk) begin
        if (rst) begin
            q <= 1'b0;
        end else if (t) begin
            q <= ~q;
        end
    end
endmodule

