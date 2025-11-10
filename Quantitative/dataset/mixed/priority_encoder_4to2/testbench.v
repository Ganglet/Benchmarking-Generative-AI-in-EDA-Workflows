`timescale 1ns / 1ps

module priority_encoder_4to2_tb;
    reg [3:0] req;
    wire [1:0] code;
    wire valid;

    priority_encoder_4to2 dut (
        .req(req),
        .code(code),
        .valid(valid)
    );

    integer i;
    reg [1:0] expected_code;
    reg expected_valid;

    initial begin
        for (i = 0; i < 16; i = i + 1) begin
            req = i[3:0];
            #1;
            expected_valid = (req != 4'b0000);
            casex (req)
                4'b1xxx: expected_code = 2'b11;
                4'b01xx: expected_code = 2'b10;
                4'b001x: expected_code = 2'b01;
                4'b0001: expected_code = 2'b00;
                default: expected_code = 2'b00;
            endcase
            if (valid !== expected_valid || code !== expected_code) begin
                $display("FAIL: req=%0b code=%0b valid=%0b expected_code=%0b expected_valid=%0b", req, code, valid, expected_code, expected_valid);
                $fatal;
            end
        end
        $display("PASS");
        $finish;
    end
endmodule

