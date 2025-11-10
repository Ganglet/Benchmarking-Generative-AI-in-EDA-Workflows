`timescale 1ns / 1ps

module johnson_counter_4bit (
    input  wire       clk,
    input  wire       rst,
    input  wire       en,
    output reg  [3:0] q
);
    always @(posedge clk) begin
        if (rst) begin
            q <= 4'b0000;
        end else if (en) begin
            q <= {~q[0], q[3:1]};
        end
    end
endmodule

