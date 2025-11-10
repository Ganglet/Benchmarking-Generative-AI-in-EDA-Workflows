`timescale 1ns / 1ps

module shift_register_4bit (
    input  wire       clk,
    input  wire       rst,
    input  wire       en,
    input  wire       serial_in,
    output reg  [3:0] q
);
    always @(posedge clk) begin
        if (rst) begin
            q <= 4'b0000;
        end else if (en) begin
            q <= {q[2:0], serial_in};
        end
    end
endmodule

