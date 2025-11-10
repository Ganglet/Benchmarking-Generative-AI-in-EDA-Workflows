`timescale 1ns / 1ps

module decoder_2to4 (
    input  wire       en,
    input  wire [1:0] in,
    output wire [3:0] out
);
    assign out = en ? (4'b0001 << in) : 4'b0000;
endmodule

